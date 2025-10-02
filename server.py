from flask import Flask, render_template, current_app, g, request, session, redirect, url_for
import os
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor
from contextlib import contextmanager
from dotenv import load_dotenv
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth


app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']


oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=os.environ.get("AUTH0_CLIENT_ID"),
    client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


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

# Auth0

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    # can check for user existence here
    session["user"] = token
    # return redirect("/")
    return redirect(url_for("hello"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + os.environ.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("hello", _external=True),
                "client_id": os.environ.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

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