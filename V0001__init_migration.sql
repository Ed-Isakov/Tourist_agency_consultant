CREATE SCHEMA IF NOT EXISTS communications;

CREATE TABLE communications.threads (
    thread_id           SERIAL PRIMARY KEY,
    dttm_inserted       TIMESTAMPTZ NOT NULL        DEFAULT NOW(),
    dttm_updated        TIMESTAMPTZ NOT NULL        DEFAULT NOW()
);

CREATE TABLE communications.users (
    user_id             SERIAL PRIMARY KEY,
    username            TEXT,
    tg_chat_id          TEXT NOT NULL,
    dttm_inserted       TIMESTAMPTZ NOT NULL        DEFAULT NOW(),
    dttm_updated        TIMESTAMPTZ NOT NULL        DEFAULT NOW(),
    forename            TEXT,
    surname             TEXT         
);

CREATE TYPE communications.author AS ENUM (
    'CONSULTANT',
    'USER'
);

CREATE TABLE communications.messages (
    message_id          SERIAL PRIMARY KEY,
    text                TEXT,
    thread_id           SERIAL NOT NULL,
    user_id             SERIAL NOT NULL,
    author              communications.author NOT NULL,
    feedback            INTEGER,
    dttm_inserted       TIMESTAMPTZ NOT NULL        DEFAULT NOW(),
    dttm_updated        TIMESTAMPTZ NOT NULL        DEFAULT NOW(),
    FOREIGN KEY (thread_id) REFERENCES
        communications.threads(thread_id)
        ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES
        communications.users(user_id)
        ON DELETE RESTRICT
);
