"""
  VULN-01b  SQL Injection      — login query built with raw string concatenation
  VULN-05   Weak password hash — MD5, no salt
  VULN-03   No lockout         — login_attempts table exists but is never read/written here
  VULN-04   Session fixation   — session not regenerated after successful login
  (no MFA)  Single-factor only — hardened branch adds /mfa/setup + /mfa/verify

"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import db, User
from app.audit import log_action
import hashlib

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    raw_query = (
        "SELECT id, username, password, user_type, lock_status "
        f"FROM users WHERE username = '{username}'"
    )
    result = db.session.execute(db.text(raw_query)).fetchone()

    if result is None:
       
        log_action("login_failed", target_type="username_attempted", after={"username": username})
        db.session.commit()
        flash("Invalid username or password.")
        return render_template("login.html")

    user_id, db_username, db_password_hash, user_type, lock_status = result

   
    submitted_hash = hashlib.md5(password.encode()).hexdigest()

    if submitted_hash != db_password_hash:
       
        log_action("login_failed", target_type="user", target_id=user_id,
                   after={"username": db_username, "reason": "wrong_password"})
        db.session.commit()
        flash("Invalid username or password.")
        return render_template("login.html")

    session["user_id"] = user_id
    session["username"] = db_username
    session["user_type"] = user_type
    # -------------------------------------------------------------------------

    log_action("login_success", target_type="user", target_id=user_id)
    db.session.commit()

    # No MFA step here in vuln-baseline -- straight to full auth.
    if user_type == "admin":
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("sales.dashboard"))


@auth_bp.route("/logout")
def logout():
    log_action("logout")
    db.session.commit()
    session.clear()
    return redirect(url_for("auth.login"))


def login_required(role=None):
   
    from functools import wraps

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if role and session.get("user_type") != role:
                return "Forbidden", 403
            return f(*args, **kwargs)
        return wrapped
    return decorator
