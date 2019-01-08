import os

from flask import Flask, redirect, render_template, session, request, flash, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import json

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

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
        return redirect("/booksearch")

@app.route("/booksearch", methods=["GET","POST"])
def booksearch():
    post_isbn = request.form.get("isbn")
    post_title = request.form.get("booktitle")
    post_author = request.form.get("author")
    if request.method == "POST":
        books = db.execute("SELECT * FROM books WHERE isbn like :isbn and lower(title) like lower(:title) and lower(author) like lower(:author)",{"isbn": '%'+post_isbn+'%',"title": '%'+post_title+'%', "author": '%'+post_author+'%'}).fetchall()
        return render_template("books.html",books=books)
    else:
        return render_template("booksearch.html")

@app.route("/books", methods=["POST"])
def books():
    return render_template("books.html")

@app.route("/book/<string:isbn>", methods=["GET"])
def book(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn": isbn}).fetchall()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "rQPXZ9RxUsOU0BkirgCzg", "isbns": "0618640150"})
    json_data = res.json()
    reviews_count = json_data['books'][0]['work_ratings_count']
    average_rating = json_data['books'][0]['average_rating']
    ##for data in json_data:
    ##    reviews_count = json_data[data][0]['work_ratings_count']
    return render_template("book.html", book=book, res=json_data,  reviews_count=reviews_count, average_rating=average_rating)

@app.route("/userform", methods=['GET','POST'])
def userform():
    return render_template("userform.html")

@app.route("/login", methods=['GET','POST'])
def login():
    post_user = request.form.get("username")
    post_password = request.form.get("password")

    if post_user != '' and post_password != '':
        if db.execute("SELECT * FROM users WHERE username = :username and password = :password",{"username": post_user, "password": post_password}).rowcount == 1:
            session['logged_in'] = True
            return index()
        else:
            session['logged_in'] = False
            return render_template("error.html", message="Incorrect User or Password.")
    else:
        return render_template("error.html",message="Email and Password are required.")

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect("/")

@app.route("/register", methods=["POST"])
def register():
    """Register User."""

    user = request.form.get("username")
    password = request.form.get("password")

    if db.execute("SELECT * FROM users WHERE username = :username",{"username": user}).rowcount == 0:
        if user != '' and password != '':
            db.execute("INSERT INTO users(username, password) VALUES (:username, :password)"
                 ,{"username": user, "password": password})
            db.commit()
        else:
            return render_template("error.html", message="Email and Password are required.")
    else:
        return render_template("error.html",message="User already registered.")
    return render_template("success.html")