from flask import Flask, render_template, current_app, g, request
import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor
from contextlib import contextmanager
from dotenv import load_dotenv


app = Flask(__name__)

pool = None
load_dotenv()

def setup():
    global pool
    if os.environ['DEV'] == 'true':
        DATABASE_URL = os.environ['DATABASE_URL_DEV']
        pool = ThreadedConnectionPool(1, 100, dsn=DATABASE_URL)

    else:
        DATABASE_URL = os.environ['DATABASE_URL']
        pool = ThreadedConnectionPool(1, 100, dsn=DATABASE_URL, sslmode='require')

    print(f"Connecting to: {DATABASE_URL}")
    # current_app.logger.info(f"creating db connection pool")

setup()

@contextmanager
def get_db_connection():
    try:
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)


@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as connection:
      cursor = connection.cursor(cursor_factory=DictCursor)
      # cursor = connection.cursor()
      try:
          yield cursor
          if commit:
              connection.commit()
      finally:
          cursor.close()


def add_guestbook_entry(name, message):

    with get_db_cursor(True) as cur:
        current_app.logger.info("Adding guestbook entry %s", name)
        cur.execute("INSERT INTO guestbook (name, message) values (%s, %s)", (name, message))


def get_guestbook_entries():
    ''' note -- result can be used as list of dictionaries'''
    with get_db_cursor() as cur:
        cur.execute("select * from guestbook")
        return cur.fetchall()


@app.route('/')
@app.route('/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)

@app.route('/guestbook', methods=["GET", "POST"])
def guestbook():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        message = request.form.get("message", "").strip()
        if name and message:
            add_guestbook_entry(name, message)
    entries = get_guestbook_entries()
    return render_template('guestbook.html', entries=entries)