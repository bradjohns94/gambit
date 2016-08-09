CREATE TABLE users (
    user_id TEXT NOT NULL, /* Google Hangouts User ID */
    conversation_id TEXT NOT NULL,
    full_name TEXT NOT NULL,
    nickname TEXT,
    privilege INTEGER DEFAULT 0,
    title TEXT,
    PRIMARY KEY(user_id, conversation_id),
    UNIQUE (user_id, conversation_id, nickname)
);

CREATE TABLE aliases (
    alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
    old TEXT UNIQUE NOT NULL,
    new TEXT NOT NULL
);

CREATE TABLE debt (
    lender TEXT NOT NULL,
    borrower TEXT NOT NULL,
    amount INTEGER NOT NULL,
    FOREIGN KEY(lender) REFERENCES user(full_name),
    FOREIGN KEY(borrower) REFERENCES user(full_name)
);

CREATE TABLE jokes (
    joke_id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    joke TEXT NOT NULL
);

CREATE TABLE karma (
    karma_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target TEXT UNIQUE NOT NULL,
    karma INTEGER NOT NULL
);

CREATE TABLE quotes (
    quote_id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote TEXT NOT NULL,
    said_by TEXT NOT NULL,
    said_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(said_by) REFERENCES user(full_name)
);

CREATE TABLE commands (
    command_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    privilege INTEGER DEFAULT 0
);
