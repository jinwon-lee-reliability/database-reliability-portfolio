SET application_name = 'lab_timeout';
BEGIN;
SET LOCAL lock_timeout = '1s';
SET LOCAL statement_timeout = '5s';
UPDATE lock_demo.accounts SET balance = balance - 10 WHERE id = 1;
COMMIT;
-- Expected SQLSTATE 55P03. ON_ERROR_STOP exits; disconnect rolls back.
-- In an interactive/application connection, issue ROLLBACK after the error.
