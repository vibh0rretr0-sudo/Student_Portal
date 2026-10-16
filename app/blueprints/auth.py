from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from ..services.auth_service import login_user, logout_user
from ..services.user_service import UserService


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

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        # If already logged in, redirect to appropriate dashboard
        role = session.get("role")
        if role == "student":
            return redirect(url_for("student.dashboard"))
        elif role == "professor":
            return redirect(url_for("professor.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        role = request.form.get("role", "student").strip()

        # Validation
        if not username:
            flash("Username is required", "error")
        elif not password:
            flash("Password is required", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters long", "error")
        elif password != confirm_password:
            flash("Passwords do not match", "error")
        elif not full_name:
            flash("Full name is required", "error")
        elif role not in ["student", "professor"]:
            flash("Please select a valid role", "error")
        else:
            # Check if username already exists
            existing_user = UserService.get_by_username(username)
            if existing_user:
                flash("Username already exists. Please choose a different one.", "error")
            else:
                # Create the user
                user, error = UserService.create_user(username, password, full_name, role, email if email else None)
                if error:
                    flash(error, "error")
                else:
                    # Log in the newly created user
                    login_result, login_error = login_user(username, password)
                    if login_error:
                        flash(f"Account created but login failed: {login_error}", "error")
                    else:
                        flash("Account created successfully!", "success")
                        # Redirect to appropriate dashboard
                        user_role = session.get("role")
                        if user_role == "student":
                            return redirect(url_for("student.dashboard"))
                        elif user_role == "professor":
                            return redirect(url_for("professor.dashboard"))
                        else:
                            return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
