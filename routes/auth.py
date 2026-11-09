
import smtplib
import ssl
from email.message import EmailMessage

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    current_app
)

from flask_login import (
    login_user,
    logout_user,
    current_user
)

from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    PasswordField,
    SubmitField
)

from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from itsdangerous import (
    URLSafeTimedSerializer,
    SignatureExpired,
    BadSignature
)

from extensions import db
from models.user import User


auth_bp = Blueprint("auth", __name__)


# ==========================================
# PASSWORD RESET TOKEN
# ==========================================

def generate_reset_token(user):

    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    return serializer.dumps(
        {
            "user_id": user.id,
            "password_hash": user.password_hash
        },
        salt="password-reset-salt"
    )


def verify_reset_token(token):

    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    try:

        data = serializer.loads(
            token,
            salt="password-reset-salt",
            max_age=1800
        )

    except (SignatureExpired, BadSignature):

        return None

    user = db.session.get(
        User,
        data.get("user_id")
    )

    if user is None:
        return None

    # Password change ke baad purana token invalid hoga.
    if user.password_hash != data.get("password_hash"):
        return None

    return user


# ==========================================
# SEND PASSWORD RESET EMAIL
# ==========================================

def send_reset_email(user):

    token = generate_reset_token(user)

    reset_url = url_for(
        "auth.reset_password",
        token=token,
        _external=True
    )

    message = EmailMessage()

    message["Subject"] = "EduSphere - Password Reset"
    message["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = user.email

    message.set_content(
        f"""
Hello {user.name},

We received a request to reset your EduSphere account password.

Click the link below to create a new password:

{reset_url}

This link will expire in 30 minutes.

If you did not request a password reset, you can safely ignore this email.

Regards,
EduSphere Team
"""
    )

    context = ssl.create_default_context()

    with smtplib.SMTP(
        current_app.config["MAIL_SERVER"],
        current_app.config["MAIL_PORT"],
        timeout=20
    ) as server:

        server.starttls(context=context)

        server.login(
            current_app.config["MAIL_USERNAME"],
            current_app.config["MAIL_PASSWORD"]
        )

        server.send_message(message)


# ==========================================
# ROLE-BASED DASHBOARD REDIRECT
# ==========================================

def redirect_to_dashboard(user):

    if user.role == "admin":

        return redirect(
            url_for("admin_dashboard")
        )

    elif user.role == "teacher":

        return redirect(
            url_for("teacher_dashboard")
        )

    elif user.role == "student":

        return redirect(
            url_for("student_dashboard")
        )

    # Unknown role: logout and return home.
    logout_user()

    flash(
        "Your account has an invalid role. Please contact Admin.",
        "danger"
    )

    return redirect(
        url_for("home")
    )


# ==========================================
# LOGIN FORM
# ==========================================

class LoginForm(FlaskForm):

    registration_number = StringField(
        "University Registration Number",
        validators=[
            DataRequired(),
            Length(max=50)
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired()
        ]
    )

    submit = SubmitField("Login")


# ==========================================
# STUDENT REGISTRATION FORM
# ==========================================

class RegisterForm(FlaskForm):

    name = StringField(
        "Full Name",
        validators=[
            DataRequired(),
            Length(min=3, max=100)
        ]
    )

    email = StringField(
        "Email Address",
        validators=[
            DataRequired(),
            Email(),
            Length(max=120)
        ]
    )

    registration_number = StringField(
        "University Registration Number",
        validators=[
            DataRequired(),
            Length(min=3, max=50)
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8)
        ]
    )

    submit = SubmitField("Create Student Account")


# ==========================================
# FORGOT PASSWORD FORM
# ==========================================

class ForgotPasswordForm(FlaskForm):

    email = StringField(
        "Email Address",
        validators=[
            DataRequired(),
            Email(),
            Length(max=120)
        ]
    )

    submit = SubmitField("Send Reset Link")


# ==========================================
# RESET PASSWORD FORM
# ==========================================

class ResetPasswordForm(FlaskForm):

    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8)
        ]
    )

    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo(
                "password",
                message="Passwords must match."
            ),
            Length(min=8)
        ]
    )

    submit = SubmitField("Reset Password")


# ==========================================
# LOGIN ROUTE
# ==========================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:

        return redirect_to_dashboard(current_user)

    form = LoginForm()

    if form.validate_on_submit():

        registration_number = (
            form.registration_number.data.strip()
        )

        user = User.query.filter_by(
            registration_number=registration_number
        ).first()

        if user and check_password_hash(
            user.password_hash,
            form.password.data
        ):

            # Check account status.
            if not user.is_active:

                flash(
                    "Your account has been deactivated. "
                    "Please contact Admin.",
                    "danger"
                )

                return redirect(
                    url_for("auth.login")
                )

            # Login successful.
            login_user(user)

            flash(
                "Login successful!",
                "success"
            )

            return redirect_to_dashboard(user)

        # Invalid credentials.
        flash(
            "Invalid registration number or password.",
            "danger"
        )

    return render_template(
        "auth/login.html",
        form=form
    )


# ==========================================
# STUDENT REGISTRATION ROUTE
# ==========================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:

        return redirect_to_dashboard(current_user)

    form = RegisterForm()

    if form.validate_on_submit():

        email = (
            form.email.data.strip().lower()
        )

        registration_number = (
            form.registration_number.data.strip()
        )

        existing_email = User.query.filter_by(
            email=email
        ).first()

        existing_registration = User.query.filter_by(
            registration_number=registration_number
        ).first()

        if existing_email:

            flash(
                "This email is already registered.",
                "danger"
            )

        elif existing_registration:

            flash(
                "This university registration number is already registered.",
                "danger"
            )

        else:

            new_user = User(
                name=form.name.data.strip(),
                email=email,
                registration_number=registration_number,
                password_hash=generate_password_hash(
                    form.password.data
                ),
                role="student",
                is_active=True
            )

            db.session.add(new_user)
            db.session.commit()

            flash(
                "Account created! Please log in using your registration number.",
                "success"
            )

            return redirect(
                url_for("auth.login")
            )

    return render_template(
        "auth/register.html",
        form=form
    )


# ==========================================
# FORGOT PASSWORD ROUTE
# ==========================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if current_user.is_authenticated:

        return redirect_to_dashboard(current_user)

    form = ForgotPasswordForm()

    if form.validate_on_submit():

        email = (
            form.email.data.strip().lower()
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user:

            try:

                send_reset_email(user)

            except Exception:

                current_app.logger.exception(
                    "Password reset email could not be sent."
                )

        # Same response whether email exists or not.
        flash(
            "If an account exists with this email, "
            "a password reset link will be sent to it.",
            "info"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/forgot_password.html",
        form=form
    )


# ==========================================
# RESET PASSWORD ROUTE
# ==========================================

@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    if current_user.is_authenticated:

        return redirect_to_dashboard(current_user)

    user = verify_reset_token(token)

    if user is None:

        flash(
            "This password reset link is invalid or expired. "
            "Please request a new one.",
            "danger"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    form = ResetPasswordForm()

    if form.validate_on_submit():

        user.password_hash = generate_password_hash(
            form.password.data
        )

        db.session.commit()

        flash(
            "Your password has been reset successfully. "
            "You can now log in.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html",
        form=form
    )


# ==========================================
# LOGOUT ROUTE
# ==========================================

@auth_bp.route("/logout", methods=["POST"])
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )
