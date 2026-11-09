
import secrets
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    request,
    session,
    url_for
)
from flask_login import current_user, login_required
from google_auth_oauthlib.flow import Flow

from services.google_drive_service import (
    TOKEN_FILE,
    save_credentials,
    is_drive_connected
)


google_drive_bp = Blueprint("google_drive", __name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CLIENT_SECRET_FILE = BASE_DIR / "google_credentials.json"

SCOPES = ["https://www.googleapis.com/auth/drive.file"]

REDIRECT_URI = "http://127.0.0.1:5000/oauth2callback"


def admin_required():
    return (
        current_user.is_authenticated
        and current_user.role == "admin"
    )


def admin_dashboard_redirect():
    return redirect(url_for("admin.users"))


@google_drive_bp.route("/admin/google-drive/connect")
@login_required
def connect_google_drive():

    if not admin_required():
        flash("Only Admin can connect Google Drive.", "danger")
        return admin_dashboard_redirect()

    if not CLIENT_SECRET_FILE.exists():
        flash("Google credentials file is missing.", "danger")
        return admin_dashboard_redirect()

    try:
        flow = Flow.from_client_secrets_file(
            str(CLIENT_SECRET_FILE),
            scopes=SCOPES
        )

        flow.redirect_uri = REDIRECT_URI

        # Generate a PKCE verifier for this OAuth attempt.
        code_verifier = secrets.token_urlsafe(64)
        flow.code_verifier = code_verifier

        authorization_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )

        # Store OAuth state and verifier in the Flask session.
        session["google_oauth_state"] = state
        session["google_code_verifier"] = code_verifier

        return redirect(authorization_url)

    except Exception:
        current_app.logger.exception(
            "Google Drive authorization setup failed"
        )
        flash(
            "Could not start Google Drive connection. "
            "Check the server error log.",
            "danger"
        )
        return admin_dashboard_redirect()


@google_drive_bp.route("/oauth2callback")
@login_required
def oauth2callback():

    if not admin_required():
        flash("Only Admin can connect Google Drive.", "danger")
        return admin_dashboard_redirect()

    if request.args.get("error"):
        session.pop("google_oauth_state", None)
        session.pop("google_code_verifier", None)

        flash("Google Drive connection was cancelled.", "warning")
        return admin_dashboard_redirect()

    saved_state = session.pop("google_oauth_state", None)
    saved_code_verifier = session.pop(
        "google_code_verifier",
        None
    )

    if not saved_state or not saved_code_verifier:
        flash(
            "OAuth session expired. Please try connecting again.",
            "danger"
        )
        return admin_dashboard_redirect()

    if not CLIENT_SECRET_FILE.exists():
        flash("Google credentials file is missing.", "danger")
        return admin_dashboard_redirect()

    try:
        flow = Flow.from_client_secrets_file(
            str(CLIENT_SECRET_FILE),
            scopes=SCOPES,
            state=saved_state
        )

        flow.redirect_uri = REDIRECT_URI
        flow.code_verifier = saved_code_verifier

        flow.fetch_token(
            authorization_response=request.url
        )

        save_credentials(flow.credentials)

        flash(
            "Google Drive connected successfully!",
            "success"
        )

    except Exception:
        current_app.logger.exception(
            "Google Drive OAuth callback failed"
        )
        flash(
            "Google Drive connection failed. "
            "Check the server error log.",
            "danger"
        )

    return admin_dashboard_redirect()


@google_drive_bp.route("/admin/google-drive/disconnect")
@login_required
def disconnect_google_drive():

    if not admin_required():
        flash("Only Admin can disconnect Google Drive.", "danger")
        return admin_dashboard_redirect()

    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()

    session.pop("google_oauth_state", None)
    session.pop("google_code_verifier", None)

    flash("Google Drive disconnected.", "success")
    return admin_dashboard_redirect()


@google_drive_bp.route("/admin/google-drive/status")
@login_required
def google_drive_status():

    if not admin_required():
        flash("Only Admin can view this status.", "danger")
        return admin_dashboard_redirect()

    try:
        if is_drive_connected():
            flash("Google Drive is connected.", "success")
        else:
            flash("Google Drive is not connected.", "warning")

    except Exception:
        current_app.logger.exception(
            "Google Drive status check failed"
        )
        flash(
            "Could not check Google Drive status.",
            "danger"
        )

    return admin_dashboard_redirect()
