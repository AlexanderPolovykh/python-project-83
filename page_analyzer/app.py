from flask import (
    Flask,
    flash,
    get_flashed_messages,
    render_template,
    request,
    url_for,
    redirect,
    make_response,
)
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import NamedTupleCursor
import validators
from datetime import date
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging

TIME_OUT_REQUEST = 1.0  # тайм-аут на GET-запрос к сайту

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
app.logger.setLevel(logging.DEBUG)


def urls_from_db():
    # app.logger.info("urls_from_db()")
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
            # app.logger.info(urls)
            return urls


def url_checks_from_db(id: int):
    # app.logger.info("url_checks_from_db()")
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
    # app.logger.info("url_from_db(%d)", id)
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


def url_to_db(urls: list, url_name: str) -> tuple:
    """Записать в таблицу urls новую добавленную страницу."""
    # app.logger.info("url_to_db()")
    already_exists = False
    unp = urlparse(url_name)
    for url in urls:
        np = urlparse(url.name)
        if unp.scheme == np.scheme and unp.netloc == np.netloc:  # такой сайт в базе уже есть!
            # app.logger.info("url_name: %s", url.name)
            already_exists = True
            un = url.name
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            if not already_exists:
                datestr = date.today().isoformat()
                curs.execute(
                    """
                        INSERT INTO urls (name, created_at) VALUES (%s, %s);
                    """,
                    [url_name, datestr],
                )
                curs.execute("SELECT id FROM urls WHERE name = %s;", [url_name])
            else:
                curs.execute("SELECT id FROM urls WHERE name = %s;", [un])
            rec = curs.fetchone()
            # app.logger.info("url_to_db() -> id: %d", rec.id)
    return already_exists, rec.id if rec else 0


def url_check_to_db(id: int, url_check: dict):
    """Записать в таблицу url_checks результат SEO-проверки сайта."""
    # app.logger.info("url_check_to_db()")
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
    app.logger.info("GET /")
    messages = get_flashed_messages(with_categories=True)
    mess = messages[-1] if messages else None
    return render_template("index.html", message=mess)


@app.post("/urls")
def urls_post():
    app.logger.info("POST /urls")
    new_url = request.form.get("url")
    if len(new_url) > 255 or not validators.url(new_url):
        mess = ("danger", "Некорректный URL")
        resp = make_response(render_template("index.html", message=mess))
        # flash("Некорректный URL", category="danger")
        # resp = make_response(redirect(url_for("url_input_get"), 422))
        resp.status = 422
        return resp
    else:
        urls = urls_from_db()
        exists, id = url_to_db(urls, new_url)
        # app.logger.info("id: %d", id)
        if not exists:
            flash("Страница успешно добавлена", category="success")
        else:
            flash("Страница уже существует", category="info")
        return redirect(url_for("url_get", id=id))


@app.get("/urls")
def urls_get():
    app.logger.info("GET /urls")
    urls = urls_from_db()
    messages = get_flashed_messages(with_categories=True)
    mess = messages[-1] if messages else None
    return render_template("urls.html", message=mess, urls=urls)


@app.get("/urls/<int:id>")
def url_get(id):
    app.logger.info("GET /urls/%d", id)
    url = url_from_db(id)
    url_checks = url_checks_from_db(id)
    messages = get_flashed_messages(with_categories=True)
    mess = messages[-1] if messages else None
    return render_template("urls_id.html", message=mess, url=url, url_checks=url_checks)


@app.post("/urls/<int:id>/checks")
def url_checks_post(id):
    app.logger.info("POST /urls/%d/checks", id)
    url_check = {}
    url = url_from_db(id)
    try:
        app.logger.info("before requests..")
        r = requests.get(url.name)  # , timeout=TIME_OUT_REQUEST)
        app.logger.info("after requests..")
        soup = BeautifulSoup(r.text, "html.parser")
        url_check["h1"] = soup.h1.string if soup.h1 else ""
        url_check["title"] = soup.title.string if soup.title else ""
        metas = soup.find_all("meta")
        url_check["description"] = ""
        for meta in metas:
            if meta.get("name") == "description":
                url_check["description"] = meta.get("content")
        url_check["status_code"] = r.status_code
        app.logger.info("after parsers..")
        url_check_to_db(id, url_check)
        app.logger.info("before redirect..")
        flash("Страница успешно проверена", category="success")
        return redirect(url_for("url_get", id=id))
    # except requests.exceptions.RequestException:
    except Exception:
        app.logger.info("raised Exception..")
        flash("Произошла ошибка при проверке", category="danger")
        return redirect(url_for("url_get", id=id))
