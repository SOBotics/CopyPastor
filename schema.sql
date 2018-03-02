CREATE TABLE IF NOT EXISTS posts (
 post_id INTEGER PRIMARY KEY,
 url_one text NOT NULL,
 url_two text NOT NULL,
 title_one text NOT NULL,
 title_two text NOT NULL,
 body_one text NOT NULL,
 body_two text NOT NULL,
 date_one INTEGER NOT NULL,
 date_two INTEGER NOT NULL,
 username_one text NOT NULL,
 username_two text NOT NULL,
 user_url_one text NOT NULL,
 user_url_two text NOT NULL,
 score INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback (
 feedback_id INTEGER PRIMARY KEY,
 post_id INTEGER,
 feedback_type text NOT NULL,
 username text NOT NULL,
 link text NOT NULL,
 FOREIGN KEY(post_id) REFERENCES posts(post_id)
);

CREATE TABLE IF NOT EXISTS auth (
 auth_string TEXT PRIMARY KEY,
 associated_user TEXT
);

CREATE TABLE IF NOT EXISTS reasons (
 reason_id INTEGER PRIMARY KEY,
 reason text NOT NULL
);

CREATE TABLE IF NOT EXISTS caught_for (
 post_id INTEGER NOT NULL,
 reason_id INTEGER NOT NULL,
 score INTEGER NOT NULL,
 PRIMARY KEY (post_id, reason_id),
 FOREIGN KEY(post_id) REFERENCES posts(post_id),
 FOREIGN KEY(reason_id) REFERENCES reasons(reason_id)
);
