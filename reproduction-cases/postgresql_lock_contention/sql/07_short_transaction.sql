SET application_name = 'lab_short_transaction';
BEGIN;
SET LOCAL lock_timeout = '1s';
SET LOCAL statement_timeout = '5s';
UPDATE lock_demo.accounts SET balance = balance - 10 WHERE id = 1
RETURNING id, balance;
COMMIT;
-- Perform user interaction/network calls outside the transaction.
