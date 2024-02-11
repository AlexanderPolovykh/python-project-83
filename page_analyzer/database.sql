-- DROP DATABASE page_analyzer;

-- CREATE DATABASE page_analyzer;

-- DROP TABLE IF EXISTS urls;

CREATE TABLE IF NOT EXISTS urls (
    id bigint NOT NULL GENERATED ALWAYS AS IDENTITY,
    name varchar(255),
    created_at date,
    CONSTRAINT urls_pkey PRIMARY KEY (id),
    CONSTRAINT urls_name_key UNIQUE (name)
);

INSERT INTO urls (name, created_at) 
VALUES ('https://google.com', '2024-02-09'), ('https://ru.hexlet.io', '2024-02-10');
