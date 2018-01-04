CREATE TABLE IF NOT EXISTS posts (
 post_id INTEGER PRIMARY KEY,
 url_one text NOT NULL,
 url_two text NOT NULL,
 title_one text NOT NULL,
 title_two text NOT NULL,
 body_one text NOT NULL,
 body_two text NOT NULL,
 date_one INTEGER NOT NULL,
 date_two INTEGER NOT NULL
);