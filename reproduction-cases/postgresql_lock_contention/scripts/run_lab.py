#!/usr/bin/env python3
"""Real PostgreSQL integration checks, using only Python stdlib + Docker Compose."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "sql"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class Lab:
    def __init__(self, output_root):
        self.project = "pg-lock-rca-" + uuid.uuid4().hex[:12]
        self.output = output_root / self.project
        self.output.mkdir(parents=True, exist_ok=False)
        self.compose = ["docker", "compose", "--project-name", self.project,
                        "--file", str(ROOT / "compose.yaml")]
        self.sessions = []
        self.result = {"status": "running", "started_at_utc": utc_now(),
                       "project": self.project, "scope": "synthetic independent lab",
                       "source_commit": os.environ.get("GITHUB_SHA"),
                       "ci_run_id": os.environ.get("GITHUB_RUN_ID"),
                       "assertions": []}

    def save(self, name, value):
        if not isinstance(value, str):
            value = json.dumps(value, indent=2) + "\n"
        (self.output / name).write_text(value, encoding="utf-8")

    def command(self, args, *, input_text=None, check=True, timeout=30):
        proc = subprocess.run(args, input=input_text, text=True, encoding="utf-8",
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              cwd=ROOT, timeout=timeout)
        if check and proc.returncode:
            raise RuntimeError(f"Command failed ({proc.returncode}): {args}\n"
                               f"{proc.stdout}\n{proc.stderr}")
        return proc

    def psql_command(self):
        return self.compose + ["exec", "-T", "postgres", "psql", "-X", "-q",
                               "-U", "lab", "-d", "lock_lab", "-v", "ON_ERROR_STOP=1",
                               "-v", "VERBOSITY=verbose", "-P", "pager=off"]

    def query(self, sql):
        return self.command(self.psql_command() + ["-A", "-t", "-c", sql]).stdout.strip()

    def file(self, filename, *, check=True):
        return self.command(self.psql_command() + ["-f", "/lab/sql/" + filename],
                            check=check)

    def require(self, name, condition):
        self.result["assertions"].append({"name": name, "passed": bool(condition),
                                          "captured_at_utc": utc_now()})
        if not condition:
            raise AssertionError(name)
        print("PASS: " + name, flush=True)

    def poll(self, predicate, label, timeout=15):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(0.2)
        raise TimeoutError("Timed out waiting for " + label)

    def start_session(self, filename, log_name):
        handle = (self.output / log_name).open("w", encoding="utf-8")
        try:
            proc = subprocess.Popen(self.psql_command() + ["-A", "-t"], stdin=subprocess.PIPE,
                                    stdout=handle, stderr=subprocess.STDOUT, cwd=ROOT,
                                    text=True, encoding="utf-8")
        except Exception:
            handle.close()
            raise
        self.sessions.append((proc, handle))
        proc.stdin.write((SQL / filename).read_text(encoding="utf-8") + "\n")
        proc.stdin.flush()
        return proc

    def finish_session(self, proc, ending="\\q\n"):
        proc.communicate(input=ending, timeout=10)
        return proc.returncode

    def snapshot(self, stage):
        # Each psql call is a new autocommit observer, avoiding stale tx snapshots.
        for filename, label in [("03_activity.sql", "activity"),
                                ("04_locks.sql", "locks"),
                                ("05_blocking_graph.sql", "blocking")]:
            self.save(f"{stage}-{label}.txt", self.file(filename).stdout)
        graph = json.loads(self.query("""
            SELECT coalesce(json_agg(row_to_json(g)), '[]'::json)
            FROM (
                SELECT w.pid AS waiter_pid, w.state AS waiter_state,
                       w.wait_event_type, w.wait_event,
                       p.blocker_pid, b.state AS blocker_state,
                       w.application_name AS waiter_application,
                       b.application_name AS blocker_application,
                       b.xact_start AS blocker_xact_start,
                       clock_timestamp() AS captured_at_utc
                FROM pg_stat_activity w
                CROSS JOIN LATERAL unnest(pg_blocking_pids(w.pid)) p(blocker_pid)
                LEFT JOIN pg_stat_activity b ON b.pid = p.blocker_pid
                WHERE w.datname = current_database()
                  AND w.application_name = 'lab_waiter'
            ) g;
        """))
        self.save(f"{stage}-graph.json", graph)
        return graph

    def logs(self):
        return self.command(self.compose + ["logs", "--no-color", "--timestamps", "postgres"],
                            check=False).stdout

    def blocked(self):
        return self.query("""
            SELECT EXISTS (
                SELECT 1 FROM pg_stat_activity w JOIN pg_stat_activity b
                  ON b.pid = ANY(pg_blocking_pids(w.pid))
                WHERE w.application_name = 'lab_waiter' AND w.state = 'active'
                  AND w.wait_event_type = 'Lock' AND w.wait_event = 'transactionid'
                  AND b.application_name = 'lab_blocker'
                  AND b.state = 'idle in transaction'
                  AND w.datname = current_database() AND b.datname = current_database()
            );
        """) == "t"

    def metadata(self):
        self.save("environment.txt", self.command(["docker", "version"]).stdout
                  + self.command(["docker", "compose", "version"]).stdout)
        self.save("compose-resolved.yaml", self.command(self.compose + ["config"]).stdout)
        container = self.command(self.compose + ["ps", "-q", "postgres"]).stdout.strip()
        image_id = self.command(["docker", "inspect", "--format", "{{.Image}}", container]).stdout.strip()
        image = json.loads(self.command([
            "docker", "image", "inspect", image_id, "--format", "{{json .}}"
        ]).stdout)
        self.save("image.json", image)
        self.result["postgres_image"] = {"id": image["Id"],
                                          "repo_digests": image.get("RepoDigests", [])}
        self.save("postgres-settings.txt", self.query("SELECT version();") + "\n" + self.query("""
            SELECT name || '=' || setting || coalesce(unit, '')
            FROM pg_settings WHERE name IN ('log_lock_waits', 'deadlock_timeout',
                'log_line_prefix', 'log_timezone', 'server_version',
                'transaction_isolation', 'statement_timeout',
                'lock_timeout', 'idle_in_transaction_session_timeout') ORDER BY name;
        """) + "\n")
        self.require("PostgreSQL major version is 17", self.query(
            "SELECT current_setting('server_version_num')::int / 10000 = 17;") == "t")

    def exercise(self):
        self.command(self.compose + ["up", "-d", "--wait", "--wait-timeout", "90"], timeout=120)
        self.save("setup.txt", self.file("00_setup.sql").stdout)
        self.metadata()
        blocker = self.start_session("01_blocker.sql", "blocker-session.txt")
        self.poll(lambda: self.query("""
            SELECT EXISTS (SELECT 1 FROM pg_stat_activity
                WHERE application_name = 'lab_blocker' AND datname = current_database()
                  AND state = 'idle in transaction');
        """) == "t", "blocker transaction")
        waiter = self.start_session("02_blocked.sql", "waiter-session.txt")
        self.poll(self.blocked, "blocked -> blocker relationship")
        self.require("waiter waits on transactionid held by idle-in-transaction blocker", self.blocked())
        graph = self.snapshot("before-recovery")
        self.require("captured graph identifies exactly one scenario blocker", len(graph) == 1
                     and graph[0]["blocker_application"] == "lab_blocker"
                     and graph[0]["waiter_application"] == "lab_waiter")
        self.require("pg_locks correlates ungranted ShareLock with granted transaction ExclusiveLock",
                     self.query("""
            SELECT EXISTS (
                SELECT 1 FROM pg_locks w JOIN pg_locks b
                  ON b.transactionid = w.transactionid AND b.locktype = w.locktype
                JOIN pg_stat_activity wa ON wa.pid = w.pid
                JOIN pg_stat_activity ba ON ba.pid = b.pid
                WHERE w.locktype = 'transactionid' AND NOT w.granted AND w.mode = 'ShareLock'
                  AND b.granted AND b.mode = 'ExclusiveLock' AND w.waitstart IS NOT NULL
                  AND wa.application_name = 'lab_waiter' AND ba.application_name = 'lab_blocker'
            );
        """) == "t")
        self.poll(lambda: "lab_waiter" in self.logs() and "still waiting for ShareLock" in self.logs(),
                  "server lock-wait log")
        self.save("before-recovery-server.log", self.logs())
        self.require("server emitted lock-wait evidence", "still waiting for ShareLock" in self.logs())
        visible = self.query("SELECT balance FROM lock_demo.accounts WHERE id = 1;")
        self.save("mvcc-read.txt", visible + "\n")
        self.require("ordinary SELECT sees committed 1000 while UPDATE is blocked", visible == "1000")
        independent = self.query("""
            SET statement_timeout = '5s';
            UPDATE lock_demo.accounts SET balance = balance + 1 WHERE id = 2 RETURNING balance;
        """)
        self.save("independent-row.txt", independent + "\n")
        self.require("independent row update completes", independent.splitlines()[-1] == "1001")
        timed_out = self.file("06_lock_timeout.sql", check=False)
        self.save("lock-timeout.txt", timed_out.stdout + timed_out.stderr)
        self.require("lock_timeout produces SQLSTATE 55P03", timed_out.returncode != 0
                     and "55P03" in timed_out.stderr and "lock timeout" in timed_out.stderr)
        self.require("timeout does not release the original blocking transaction", self.blocked())
        self.require("owner ROLLBACK exits cleanly", self.finish_session(blocker, "ROLLBACK;\n\\q\n") == 0)
        self.require("waiter completes and commits after rollback", self.finish_session(waiter) == 0)
        self.require("rolled-back blocker is discarded; only waiter decrement persists",
                     self.query("SELECT balance FROM lock_demo.accounts WHERE id = 1;") == "990")
        self.require("recovered graph has no blocked waiter", self.snapshot("after-recovery") == [])
        self.save("short-transaction.txt", self.file("07_short_transaction.sql").stdout)
        self.require("short transaction with local timeouts completes", self.query(
            "SELECT balance FROM lock_demo.accounts WHERE id = 1;") == "980")
        self.require("scenario sessions and lock waits are gone", self.query("""
            SELECT NOT EXISTS (SELECT 1 FROM pg_stat_activity
              WHERE datname = current_database()
                AND application_name IN ('lab_blocker', 'lab_waiter', 'lab_timeout'));
        """) == "t")
        self.save("final-verification.txt", self.file("08_verify.sql").stdout)
        self.result["final_balances"] = {"1": 980, "2": 1001}

    def run(self):
        failure = None
        try:
            self.save("result.json", self.result)
            self.exercise()
            self.result["status"] = "passed"
        except Exception as exc:
            failure = exc
            self.result.update(status="failed", error=str(exc))
            try:
                self.snapshot("failure")
            except Exception as capture_error:
                self.result["failure_capture_error"] = str(capture_error)
        finally:
            # Close only our own clients; never signal unrelated host sessions.
            for proc, handle in self.sessions:
                try:
                    if proc.poll() is None:
                        proc.communicate(input="ROLLBACK;\n\\q\n", timeout=5)
                except (subprocess.TimeoutExpired, BrokenPipeError, OSError):
                    proc.kill()
                    proc.wait(timeout=5)
                finally:
                    handle.close()
            try:
                self.save("server.log", self.logs())
                down = self.command(self.compose + ["down", "--volumes", "--remove-orphans"],
                                    check=False, timeout=30)
                self.save("cleanup.txt", down.stdout + down.stderr)
                self.result["cleanup_passed"] = down.returncode == 0
                if down.returncode:
                    raise RuntimeError("Disposable compose cleanup failed")
            except Exception as cleanup_error:
                self.result["cleanup_passed"] = False
                self.result["cleanup_error"] = str(cleanup_error)
                failure = failure or cleanup_error
                self.result["status"] = "failed"
            self.result["ended_at_utc"] = utc_now()
            self.result["files_sha256"] = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(self.output.iterdir()) if path.name != "result.json"
            }
            self.save("result.json", self.result)
            print(json.dumps(self.result, indent=2), flush=True)
            print("Evidence: " + str(self.output), flush=True)
        if failure:
            raise failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    lab = Lab(args.output_root.resolve())
    try:
        lab.run()
    except Exception as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
