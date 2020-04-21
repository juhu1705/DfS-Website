DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS characters;
DROP TABLE IF EXISTS character_information;
DROP TABLE IF EXISTS user_permissions;
DROP TABLE IF EXISTS discussion;
DROP TABLE IF EXISTS comment;
DROP TABLE IF EXISTS short_stories;
DROP TABLE IF EXISTS information_order;
DROP TABLE IF EXISTS time_event;
DROP TABLE IF EXISTS language;
DROP TABLE IF EXISTS grammar_rules;
DROP TABLE IF EXISTS word_category;
DROP TABLE IF EXISTS declination;
DROP TABLE IF EXISTS word;
DROP TABLE IF EXISTS word_declinations;
DROP TABLE IF EXISTS language_to_word_category;
DROP TABLE IF EXISTS writing;
DROP TABLE IF EXISTS letter;
DROP TABLE IF EXISTS rule;


CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    level INTEGER NOT NULL,
    pwd_hash STRING NOT NULL,
    email STRING NOT NULL,
    password_reset_token STRING,
    email_confirmed INTEGER NOT NULL,
    visible INTEGER NOT NULL,
    confirmation_token STRING
);

CREATE TABLE user_permissions (
    user_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    PRIMARY KEY (character_id, user_id),
    FOREIGN KEY (character_id) REFERENCES characters (id),
    FOREIGN KEY (user_id) REFERENCES user (id)
);

CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    family STRING NOT NULL,
    species STRING NOT NULL
);

CREATE TABLE information_order (
    position INTEGER PRIMARY KEY,
    information_title STRING NOT NULL
);

CREATE TABLE character_information (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER NOT NULL,
    title STRING NOT NULL,
    value STRING NOT NULL,
    FOREIGN KEY (character_id) REFERENCES characters (id)
);

CREATE TABLE discussion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title STRING NOT NULL,
    author INTEGER NOT NULL,
    created TIMESTAMP NOT NULL,
    FOREIGN KEY (author) REFERENCES user (id)
);

CREATE TABLE comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discussion_id NOT NULL,
    value STRING NOT NULL,
    author INTEGER NOT NULL,
    created TIMESTAMP NOT NULL,
    FOREIGN KEY (discussion_id) REFERENCES discussion (id),
    FOREIGN KEY (author) REFERENCES user (id)
);

CREATE TABLE short_stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title STRING NOT NULL,
    story STRING NOT NULL,
    author INTEGER NOT NULL,
    time TIMESTAMP NOT NULL,
    FOREIGN KEY (author) REFERENCES user (id)
);

CREATE TABLE time_event (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    athon INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    description STRING NOT NULL,
    author INTEGER NOT NULL,
    FOREIGN KEY (author) REFERENCES user (id)
);


CREATE TABLE language (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    description STRING NOT NULL,
    writing_id INTEGER,
    FOREIGN KEY (writing_id) REFERENCES writing (id)
);

CREATE TABLE grammar_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    rule STRING NOT NULL,
    description STRING,
    language_id INTEGER NOT NULL,
    FOREIGN KEY (language_id) REFERENCES language (id)
);

CREATE TABLE word_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    description STRING NOT NULL
);

CREATE TABLE declination (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    word_category_id INTEGER NOT NULL,
    FOREIGN KEY (word_category_id) REFERENCES word_category (id)
);

CREATE TABLE word_declinations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word STRING NOT NULL,
    parent_word_id INTEGER NOT NULL,
    declination_id INTEGER NOT NULL,
    FOREIGN KEY (declination_id) REFERENCES declination (id),
    FOREIGN KEY (parent_word_id) REFERENCES word (id)
);

CREATE TABLE word (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word STRING NOT NULL,
    translation STRING NOT NULL,
    description STRING,
    word_category_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    FOREIGN KEY (language_id) REFERENCES language (id),
    FOREIGN KEY (word_category_id) REFERENCES word_category (id)
);

CREATE TABLE language_to_word_category (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_category_id INTEGER NOT NULL,
    language_id INTEGER NOT NULL,
    FOREIGN KEY (language_id) REFERENCES language (id),
    FOREIGN KEY (word_category_id) REFERENCES word_category (id)
);

CREATE TABLE writing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    description STRING NOT NULL
);

CREATE TABLE letter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    latin_letter STRING NOT NULL,
    writing_id INTEGER NOT NULL,
    FOREIGN KEY (writing_id) REFERENCES writing (id)
);

CREATE TABLE rule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    rule STRING NOT NULL,
    writing_id INTEGER NOT NULL,
    FOREIGN KEY (writing_id) REFERENCES writing (id)
);