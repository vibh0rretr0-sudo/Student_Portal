from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from auth import login_user, logout_user, login_required
from database import get_user_by_id

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        role = session.get("role")
        if role == "student":
            return redirect(url_for("student.dashboard"))
        elif role == "professor":
            return redirect(url_for("professor.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user, error = login_user(username, password)
        if error:
            return render_template("login.html", error=error)

        role = session.get("role")
        if role == "student":
            return redirect(url_for("student.dashboard"))
        elif role == "professor":
            return redirect(url_for("professor.dashboard"))

    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
