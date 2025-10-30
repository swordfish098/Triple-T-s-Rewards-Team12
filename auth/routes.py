# auth/routes.py
import base64
from io import BytesIO
from urllib.parse import urlparse, urljoin
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
import pyotp
import qrcode
import auth
from models import User, Role  # Role has DRIVER, SPONSOR, ADMINISTRATOR
from datetime import datetime, timedelta
from extensions import db
from sqlalchemy import or_
from common.logging import log_audit_event, LOGIN_EVENT
from . import auth_bp

auth_bp = Blueprint("auth", __name__, template_folder="../templates")


LOCKOUT_ATTEMPTS = 3
RESET_TOKEN_TTL_MINUTES = 30



@auth_bp.route('/settings')
@login_required
def settings():
    return render_template('auth/settings.html')


@auth_bp.route("/twofa/setup", methods=["GET"])
@login_required
def twofa_setup():
    if not current_user.TOTP_SECRET:
        current_user.TOTP_SECRET = pyotp.random_base32()
        from extensions import db
        db.session.commit()

    uri = f"otpauth://totp/TripleTsRewards:{current_user.USERNAME}?secret={current_user.TOTP_SECRET}&issuer=TripleTsRewards"
    img = qrcode.make(uri)
    buf = BytesIO()
    img.save(buf, format="PNG")
    qr_data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    return render_template("auth/setup_2fa.html", qr_data_url=qr_data_url, secret=current_user.TOTP_SECRET)


def dashboard_endpoint_redirect(user) -> str:
    mapping = {
        Role.ADMINISTRATOR: "administrator_bp.dashboard",
        Role.SPONSOR: "sponsor_bp.dashboard",
        Role.DRIVER: "driver_bp.dashboard",
    }
    return mapping.get(user.USER_TYPE, "common.index")
# auth/routes.py
@auth_bp.route("/twofa/verify", methods=["POST"])
@login_required
def twofa_verify():
    token = (request.form.get("token") or "").strip()
    if not current_user.TOTP_SECRET:
        flash("No 2FA setup in progress.", "warning")
        return redirect(url_for("auth.twofa_setup"))

    totp = pyotp.TOTP(current_user.TOTP_SECRET)
    if totp.verify(token, valid_window=1):
        current_user.TOTP_ENABLED = True  # if you added this column
        from extensions import db
        db.session.commit()
        endpoint_redirect = dashboard_endpoint_redirect(current_user)
        flash("Two-factor authentication is enabled.", "success")
        return redirect(url_for(endpoint_redirect))  # Whatever your dashboard is
    else:
        flash("Invalid code. Please try again.", "danger")
        return redirect(url_for("auth.twofa_setup"))

def _is_safe_url(target: str) -> bool:
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc

def _redirect_by_role(user):
    role = getattr(user, "USER_TYPE", None)
    if role == Role.ADMINISTRATOR:
        return redirect(url_for("administrator_bp.dashboard"))
    if role == Role.SPONSOR:
        return redirect(url_for("sponsor_bp.dashboard"))
    # default → driver
    return redirect(url_for("driver_bp.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(USERNAME=username).first()
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        
        if not user:
            flash("Invalid username or password", "danger")
            log_audit_event(LOGIN_EVENT, f"FAIL user={username} ip={ip}")
            return render_template("common/login.html")
        
        if user.is_account_locked():
            if user.LOCKED_REASON == "admin":
                until = user.LOCKOUT_TIME.strftime("%Y-%m-%d %H:%M:%S") if user.LOCKOUT_TIME else "later"
                flash(f"Your account has been locked by an administrator until {until}.", "danger")
                log_audit_event(LOGIN_EVENT, f"user={user.USERNAME} ip={ip} reason=locked")
                return render_template("common/login.html")
            else:
                flash("Account locked. Please Contact your Administrator.", "danger")
                log_audit_event(LOGIN_EVENT, f"user={user.USERNAME} ip={ip} reason=locked")
                return render_template("common/login.html")
        
        if not user.check_password(password):
            user.register_failed_attempt()
            db.session.commit()
            remaining = max(0, LOCKOUT_ATTEMPTS - user.FAILED_ATTEMPTS)
            flash(f"Invalid username or password. {remaining} attempts remaining.", "danger")
            log_audit_event(LOGIN_EVENT, f"user={user.USERNAME} ip={ip} attempts={user.FAILED_ATTEMPTS}")
            return render_template("common/login.html")
        
        
        #on successful login
        user.clear_failed_attempts()
        db.session.commit()
        login_user(user)
        flash("Login successful!", "success")
        log_audit_event(LOGIN_EVENT, f"user={user.USERNAME} role={user.USER_TYPE} ip={ip}")
        
        next_page = request.args.get("next")
        if next_page and _is_safe_url(next_page):
            return redirect(next_page)
        return _redirect_by_role(user)
    return render_template("common/login.html")  # a shared login template
    
    
@auth_bp.get("/logout")
@login_required
def logout():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    # capture BEFORE logging out
    uname = current_user.USERNAME
    urole = current_user.USER_TYPE

    # log first while we still have the user info
    log_audit_event(LOGIN_EVENT, f"user={uname} role={urole} ip={ip}")

    # then perform the logout
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))




@auth_bp.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        user = User.query.filter_by(USERNAME=identifier).first()
        if not user:
            flash("Username not found.", "danger")
            return render_template("common/reset_password.html")
        
        token = user.generate_reset_token()
        db.session.commit()
        
        reset_url = url_for("auth.reset_token", token=token, _external=True)
        flash(f"Password reset link (valid for {RESET_TOKEN_TTL_MINUTES} minutes): {reset_url}", "info")
        log_audit_event("RESET REQUEST", f"Password reset requested for user {user.USERNAME}.")
        return redirect(url_for("auth.reset_password"))
    return render_template("common/reset_password.html")

def reset_request():
    if request.method == "POST":
        identifier = request.form.get("username", "").strip()
        user = User.query.filter(or_(User.USERNAME == identifier, User.USERNAME== identifier)).first()
        if not user:
            flash("Username not found.", "danger")
            return render_template("common/reset_password.html")
        token = user.generate_reset_token()
        db.session.commit()
        
        reset_url = url_for("auth.reset_token", token=token, _external=True)
        flash(f"Password reset link (valid for {RESET_TOKEN_TTL_MINUTES} minutes): {reset_url}", "info")
        return redirect(url_for("auth.reset_password"))
    
    
@auth_bp.route("/reset/<token>", methods=["GET", "POST"])
def reset_token(token: str):
    user = User.query.filter_by(RESET_TOKEN=token).first()

    if not user or not user.RESET_TOKEN_CREATED_AT:
        flash("Invalid or expired token.", "danger")
        return redirect(url_for("auth.reset_password"))

    if datetime.utcnow() > user.RESET_TOKEN_CREATED_AT + timedelta(minutes=RESET_TOKEN_TTL_MINUTES):
        user.clear_reset_token()
        db.session.commit()
        flash("Token has expired Please request a new one.", "warning")
        log_audit_event("RESET EXPIRED", f"Password reset token expired for user {user.USERNAME}.")
        return redirect(url_for("auth.reset_password"))
    
    if request.method == "POST":
        new_password = request.form.get("password","")
        confirm_password = request.form.get("confirm_password","")
        
        if not new_password or new_password != confirm_password:
            flash("Passwords do not match or are empty.", "danger")
            return render_template("common/reset_with_token.html", token=token)
        
        user.set_password(new_password)
        user.clear_reset_token()
        user.clear_failed_attempts()  # also clear failed attempts on password reset
        db.session.commit()
        
        flash("Password has been reset. You can now log in.", "success")
        log_audit_event("RESET SUCCESS", f"Password reset successful for user {user.USERNAME}.")
        return redirect(url_for("auth.login"))
    
    return render_template("common/reset_with_token.html", token=token)
