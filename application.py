import os

from flask import Flask, redirect, render_template, session, request, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import LoginManager

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

login = LoginManager(app)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/",  methods=["GET"])
def index():
    if not session.get('logged_in'):
        return  render_template("login.html")
    else:
        return render_template("booksearch.html")

@app.route("/userform", methods=['GET','POST'])
def userform():
    return render_template("userform.html")

@app.route("/login", methods=['GET','POST'])
def login():
    post_user = request.form.get("username")
    post_password = request.form.get("password")

    if db.execute("SELECT * FROM users WHERE username = :username and password = :password",{"username": post_user, "password": post_password}).rowcount == 1:
        return index()

@app.route("/register", methods=["GET"])
def register():
    """Register User."""

    user = request.form.get("username")
    password = request.form.get("password")

    if db.execute("SELECT * FROM users WHERE username = :username",{"username": user}).rowcount == 0:
        db.execute("INSERT INTO users(username, password) VALUES (:username, :password)"
                 ,{"username": user, "password": password})
        db.commit()
    else:
        return render_template("error.html",message="User already registered.")
    return render_template("success.html")

