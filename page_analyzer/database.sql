-- DROP DATABASE page_analyzer;

-- CREATE DATABASE page_analyzer;

DROP TABLE IF EXISTS url_checks;

DROP TABLE IF EXISTS urls;

CREATE TABLE urls (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255) UNIQUE,
    created_at date
);


CREATE TABLE url_checks (
    id integer PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id integer REFERENCES urls (id),
    status_code smallint,
    h1 varchar(255),
    title varchar(255),
    description varchar(255),
    created_at date
);

INSERT INTO urls (name, created_at) 
VALUES 
    ('https://google.com', '2024-02-09'), 
    ('https://ru.hexlet.io', '2024-02-10'),
    ('https://e.mail.ru', '2024-02-11');
