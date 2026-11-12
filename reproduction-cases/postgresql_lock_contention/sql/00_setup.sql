-- Reset only the dedicated synthetic lab table, after all lab sessions exit.
CREATE SCHEMA IF NOT EXISTS lock_demo;
CREATE TABLE IF NOT EXISTS lock_demo.accounts (
    id integer PRIMARY KEY,
    balance integer NOT NULL CHECK (balance >= 0),
    note text NOT NULL
);
TRUNCATE lock_demo.accounts;
INSERT INTO lock_demo.accounts VALUES
    (1, 1000, 'synthetic hot account'),
    (2, 1000, 'synthetic independent account');
