from flask import Flask, flash, get_flashed_messages, render_template, request, url_for, redirect
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import NamedTupleCursor
import validators
from datetime import date
import requests
from bs4 import BeautifulSoup

TIME_OUT_REQUEST = 1.0  # тайм-аут на GET-запрос к сайту

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
# app.logger.setLevel(logging.DEBUG)


def urls_from_db():
    app.logger.info("urls_from_db()")
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute(
                """
                    SELECT id, name, (
                        SELECT max(created_at) AS last_check FROM url_checks
                        WHERE url_id = urls.id
                    ),
                    (
                        SELECT status_code FROM url_checks
                        WHERE url_id = urls.id
                        ORDER BY id DESC
                        LIMIT 1
                    )
                    FROM urls
                    ORDER BY id DESC;
                """,
            )
            urls = curs.fetchall()
            app.logger.info(urls)
            return urls


def url_checks_from_db(id: int):
    app.logger.info("url_checks_from_db()")
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            curs.execute(
                """
                    SELECT * FROM url_checks
                    WHERE url_id = %s
                    ORDER BY id DESC;
                """,
                [id],
            )
            url_checks = curs.fetchall()
            return url_checks


def url_from_db(id: int):
    app.logger.info("url_from_db(%d)", id)
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            # app.logger.info("id: %d", id)
            curs.execute(
                """
                    SELECT * FROM urls
                    WHERE id = %s;
                """,
                [id],
            )
            url = curs.fetchone()
            return url


def url_to_db(urls: list, url_name: str) -> bool:
    app.logger.info("url_to_db()")
    for url in urls:
        if url.name == url_name:
            app.logger.info("url_name: %s", url.name)
            return False
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            datestr = date.today().isoformat()
            # app.logger.info("url_name: %s, datestr: %s", url_name, datestr)
            curs.execute(
                """
                    INSERT INTO urls (name, created_at) VALUES (%s, %s);
                """,
                [url_name, datestr],
            )
    return True


def url_check_to_db(id: int, url_check: dict):
    """Записать в таблицу url_checks результат SEO-проверки сайта."""
    app.logger.info("url_check_to_db()")
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            datestr = date.today().isoformat()
            curs.execute(
                """
                    INSERT INTO url_checks 
                    (url_id, status_code, h1, title, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s);
                """,
                [
                    id,
                    url_check.get("status_code"),
                    url_check.get("h1"),
                    url_check.get("title"),
                    url_check.get("description"),
                    datestr,
                ],
            )


@app.get("/")
def url_input_get():
    app.logger.info("url_input_get()")
    messages = get_flashed_messages(with_categories=True)
    mess = messages[-1] if messages else None
    return render_template("index.html", message=mess)


@app.post("/urls")
def urls_post():
    app.logger.info("urls_post()")
    new_url = request.form.get("url")
    if len(new_url) > 255 or not validators.url(new_url):
        flash("Некорректный URL", category="danger")
        return redirect(url_for("url_input_get"))
    else:
        urls = urls_from_db()
        if url_to_db(urls, new_url):
            flash("Страница успешно добавлена", category="success")
        else:
            flash("Страница уже существует", category="info")
        return redirect(url_for("urls_get"))


@app.get("/urls")
def urls_get():
    app.logger.info("urls_get()")
    urls = urls_from_db()
    messages = get_flashed_messages(with_categories=True)
    mess = messages[-1] if messages else None
    return render_template("urls.html", message=mess, urls=urls)


@app.get("/urls/<int:id>")
def url_get(id):
    app.logger.info("url_get(%d)", id)
    url = url_from_db(id)
    url_checks = url_checks_from_db(id)
    messages = get_flashed_messages(with_categories=True)
    mess = messages[-1] if messages else None
    return render_template("urls_id.html", message=mess, url=url, url_checks=url_checks)


@app.post("/urls/<int:id>/checks")
def url_checks_post(id):
    app.logger.info("url_checks_post(%d)", id)
    url_check = {}
    url = url_from_db(id)
    try:
        r = requests.get(url.name, timeout=TIME_OUT_REQUEST)
        soup = BeautifulSoup(r.text, "html.parser")
        if soup.h1:
            url_check["h1"] = soup.h1.string
            app.logger.info("h1: %s", url_check.get("h1"))
        if soup.title:
            url_check["title"] = soup.title.string
        if soup.meta and soup.meta.get("name") == "description":
            url_check["description"] = soup.meta.get("content")
        url_check["status_code"] = r.status_code
        url_check_to_db(id, url_check)
        return redirect(url_for("url_get", id=id))
    except requests.exceptions.RequestException:
        flash("Произошла ошибка при проверке", category="danger")
        return redirect(url_for("url_get", id=id))
