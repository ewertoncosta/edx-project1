import os

from flask import Flask, redirect, render_template, session, request, flash, url_for
from flask_session import Session
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
import json
from datetime import datetime

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
    if 'username' in session:
        return redirect("/booksearch")
    else:
        return  render_template("login.html")

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

@app.route("/book/<string:isbn>", methods=["GET","POST"])
def book(isbn):
    """Get user input"""
    review = request.form.get("textreview")
    rating = request.form.get("textrating")

    """Return book data from the database"""
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",{"isbn": isbn}).fetchall()
    book_id = [column[0] for column in book]

    """Return review data from the database"""
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id",{"book_id": book_id[0]}).fetchall()
    payload = {'key': 'rQPXZ9RxUsOU0BkirgCzg', 'isbns': isbn}

    """Get Request on GoodReads API"""
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params=payload)
    json_data = res.json()
    reviews_count = json_data['books'][0]['work_ratings_count']
    average_rating = json_data['books'][0]['average_rating']

    current_date = datetime.now()

    if request.method == "POST":
        if review != '':
            try:
                db.execute("INSERT INTO reviews(book_id,review,rating,username,date) VALUES (:book_id, :review, :rating, :username, :date)"
                        ,{"book_id": book_id[0], "review": review, "rating": rating, "username": session.get("username"), "date": current_date})
                db.commit()
                reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id",{"book_id": book_id[0]}).fetchall()
                return redirect(url_for('book',isbn=isbn))
            except exc.IntegrityError as e:
                db.rollback()
                return render_template("error.html",message="Cannot submit more than 1 review per user.")
            
    return render_template("book.html", book=book, res=json_data,  reviews_count=reviews_count, average_rating=average_rating, reviews=reviews)            

@app.route("/userform", methods=['GET','POST'])
def userform():
    return render_template("userform.html")

@app.route("/login", methods=['GET','POST'])
def login():
    post_user = request.form.get("username")
    post_password = request.form.get("password")

    if post_user != '' and post_password != '':
        if db.execute("SELECT * FROM users WHERE username = :username and password = :password",{"username": post_user, "password": post_password}).rowcount == 1:
            session['username'] = post_user
            return index()
        else:
            session.pop('username', None)
            return render_template("error.html", message="Incorrect User or Password.")
    else:
        return render_template("error.html",message="Email and Password are required.")

@app.route("/logout")
def logout():
    session.pop('username', None)
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

@app.route("/api/<string:isbn>", methods=["GET"])
def api(isbn):
    response = db.execute("SELECT books.title,  books.author,  books.year,  round(avg(reviews.rating),1) average_rating,  count(*) review_count  FROM books join reviews ON books.id = reviews.book_id WHERE books.isbn =  :isbn group by books.isbn    ,  books.title    ,  books.author    ,  books.year",{"isbn": isbn}).fetchall()
    
    return response

