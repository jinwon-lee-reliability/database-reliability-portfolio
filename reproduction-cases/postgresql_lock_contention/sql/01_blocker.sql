SET application_name = 'lab_blocker';
SET statement_timeout = '45s';
SET idle_in_transaction_session_timeout = '120s';
BEGIN;
UPDATE lock_demo.accounts SET balance = balance - 100 WHERE id = 1;
SELECT pg_backend_pid() AS blocker_pid;
-- Keep THIS connection open. Run ROLLBACK in this session after capture.
-- Executing this file with psql -f alone exits and releases the lock.
