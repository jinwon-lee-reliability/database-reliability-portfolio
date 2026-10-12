SET application_name = 'lab_waiter';
BEGIN;
SET LOCAL statement_timeout = '45s';
UPDATE lock_demo.accounts SET balance = balance - 10 WHERE id = 1
RETURNING id, balance;
COMMIT;
\echo waiter_done
