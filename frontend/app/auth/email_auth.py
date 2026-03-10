# Email/Password authentication blueprint
import re
import uuid

from app.extensions import db
from app.models import User
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

email_auth = Blueprint("email_auth", __name__)


def is_valid_email(email):
    """Basic email validation"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_strong_password(password):
    """Check if password meets minimum requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"


@email_auth.route("/register", methods=["GET", "POST"])
def register():
    """User registration with email and password"""
    if current_user.is_authenticated:
        return redirect(url_for("main.workspace"))

    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        errors = []

        if not first_name:
            errors.append("First name is required")

        if not email:
            errors.append("Email is required")
        elif not is_valid_email(email):
            errors.append("Please enter a valid email address")

        if not password:
            errors.append("Password is required")
        else:
            is_strong, message = is_strong_password(password)
            if not is_strong:
                errors.append(message)

        if password != confirm_password:
            errors.append("Passwords do not match")

        # Check if email already exists
        if email and User.query.filter_by(email=email).first():
            errors.append("An account with this email already exists")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("auth/register.html")

        try:
            user = User()
            user.id = str(uuid.uuid4())
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.auth_type = "email"
            user.is_email_verified = False
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            # Log in the user
            login_user(user)
            flash(
                f"Welcome {first_name}! Your account has been created successfully.",  # noqa
                "success",
            )
            return redirect(url_for("main.workspace"))

        except Exception as e:  # noqa
            db.session.rollback()
            flash(
                "An error occurred while creating your account. Please try again.",  # noqa
                "error",
            )
            return render_template("auth/register.html")

    return render_template("auth/register.html")


@email_auth.route("/login", methods=["GET", "POST"])
def login():
    """User login with email and password"""
    if current_user.is_authenticated:
        return redirect(url_for("main.workspace"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember_me = request.form.get("remember_me") == "on"

        if not email or not password:
            flash("Please enter both email and password", "error")
            return render_template("auth/login.html")

        # Find user by email
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with this email address", "error")
            return render_template("auth/login.html")

        if user.auth_type != "email":
            flash(
                "This account was created with Google. Please use Google sign-in.",  # noqa
                "error",
            )
            return render_template("auth/login.html")

        if not user.check_password(password):
            flash("Incorrect password", "error")
            return render_template("auth/login.html")

        login_user(user, remember=remember_me)
        flash(f"Welcome back, {user.first_name}!", "success")

        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("main.workspace"))

    return render_template("auth/login.html")


@email_auth.route("/logout")
def logout():
    """Logout user"""
    logout_user()
    flash("You have been logged out successfully", "info")
    return redirect(url_for("main.index"))


@email_auth.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Password reset request (placeholder for now)"""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email:
            flash("Please enter your email address", "error")
            return render_template("auth/forgot_password.html")

        user = User.query.filter_by(email=email, auth_type="email").first()

        if user:
            # TODO: Implement email-based password reset
            # For now, just show a message
            flash(
                "If an account with this email exists, you will receive password reset instructions.",  # noqa
                "info",
            )
        else:
            flash(
                "If an account with this email exists, you will receive password reset instructions.",  # noqa
                "info",
            )

        return redirect(url_for("email_auth.login"))

    return render_template("auth/forgot_password.html")
