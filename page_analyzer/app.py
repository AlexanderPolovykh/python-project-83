from flask import Flask, flash, get_flashed_messages, render_template, request, url_for, redirect
from dotenv import load_dotenv
import os

import psycopg2
from psycopg2.extras import NamedTupleCursor
import validators
from datetime import date

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
# app.logger.setLevel(logging.DEBUG)


def urls_from_db():
    app.logger.info("urls_from_db()")
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            # app.logger.info(curs.name)
            curs.execute(
                """
                    SELECT * FROM urls
                    ORDER BY id DESC;
                """
            )
            urls = curs.fetchall()
            return urls


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


def url_to_db(url_name: str) -> bool:
    app.logger.info("url_to_db()")
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=NamedTupleCursor) as curs:
            datestr = date.today().isoformat()
            # app.logger.info("url_name: %s, datestr: %s", url_name, datestr)
            try:
                curs.execute(
                    """
                        INSERT INTO urls (name, created_at) VALUES ('%s', '%s');
                    """,
                    [url_name, datestr],
                )
            except Exception:
                return False
    return True


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
        if url_to_db(new_url):
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
    messages = get_flashed_messages(with_categories=True)
    mess = messages[-1] if messages else None
    return render_template("urls_id.html", message=mess, url=url)
