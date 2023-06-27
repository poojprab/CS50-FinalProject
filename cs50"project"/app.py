import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import login_required, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    cash_dis = db.execute("SELECT balance FROM users WHERE id = ?", user_id)
    cash = cash_dis[0]["balance"]

    return render_template("index.html", cash = cash, user_id = user_id)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        user_id = session["user_id"]
        balance = db.execute("SELECT balance FROM users WHERE id = ?", user_id)
        balance = balance[0]["balance"]
        amount = int(request.form.get("symbol"))
        if not amount:
            flash("Invalid Amount!")

        newcash = (balance + amount)

        db.execute("UPDATE users SET balance = ? WHERE id = ?", newcash, user_id)

        date = datetime.datetime.now()

        db.execute("INSERT INTO transactions (user_id, withdrawals, deposits, date) VALUES (?, ?, ?, ?)", user_id, 0, amount, date)

        flash("Success!")

        return redirect("/")

    else:
        return render_template("deposit.html")


@app.route("/history")
@login_required
def history():
    user_id = session["user_id"]
    transactions_dis = db.execute("SELECT withdrawals, deposits, date FROM transactions WHERE user_id = ?", user_id)
    return render_template("history.html", database = transactions_dis)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Must provide username!")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must provide password!")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template('error.html', message = "Incorrect Username and/or Password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    #make sure username exists, required
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template('error.html', message = "Must provide Username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template('error.html', message = "Must providePassword")

        if not request.form.get("password") == request.form.get("confirmation"):
            return render_template('error.html', message = "Passwords do not match!")

        try:
            new = db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
        except:
            return render_template('error.html', message = "Username already exists!")

        # Remember which user has logged in
        session["user_id"] = new

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")

@app.route("/change", methods=["GET", "POST"])
def change():
    #make sure username exists, required
    # Ensure username was submitted
    if request.method == "POST":
        if not request.form.get("username"):
            return render_template('error.html', message = "Must provide Username!")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template('error.html', message = "Must provide Password!")

        if not request.form.get("password") == request.form.get("confirmation"):
            return render_template('error.html', message = "Passwords do not match!")

        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1:
            return render_template('error.html', message = "Invalid Username")

        new = db.execute("UPDATE users SET hash = ? WHERE username = ?", generate_password_hash(request.form.get("password")), request.form.get("username"))

        # Remember which user has logged in
        flash("Password Changed!")

        # Redirect user to home page
        return redirect("/")
    else:
        return render_template("changepass.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "POST":
        user_id = session["user_id"]
        amount = int(request.form.get("shares"))
        balance = db.execute("SELECT balance FROM users WHERE id = ?", user_id)
        balance = balance[0]["balance"]

        if not amount:
           return render_template('error.html', message = "Invalid Amount!")

        if amount > balance:
            return render_template('error.html', message = "Not enough Balance!")

        newcash = balance - amount

        db.execute("UPDATE users SET balance = ? WHERE id = ?", newcash, user_id)

        date = datetime.datetime.now()

        db.execute("INSERT INTO transactions (user_id, withdrawals, deposits, date) VALUES (?, ?, ?, ?)", user_id, amount, 0, date)

        flash("Success!")

        return redirect("/")

    else:
        return render_template("withdraw.html")
