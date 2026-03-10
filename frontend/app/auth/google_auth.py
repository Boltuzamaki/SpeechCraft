# Google OAuth authentication blueprint
import json
import os
import uuid

import requests
from app.extensions import db
from app.models import User
from flask import Blueprint, flash, redirect, request, url_for
from flask_login import login_user, logout_user  # noqa
from oauthlib.oauth2 import WebApplicationClient

# TODO: Set these environment variables in your Replit secrets
# GOOGLE_OAUTH_CLIENT_ID = "your-google-client-id"
# GOOGLE_OAUTH_CLIENT_SECRET = "your-google-client-secret"

GOOGLE_CLIENT_ID = os.environ.get(
    "GOOGLE_OAUTH_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID_HERE"
)
GOOGLE_CLIENT_SECRET = os.environ.get(
    "GOOGLE_OAUTH_CLIENT_SECRET", "YOUR_GOOGLE_CLIENT_SECRET_HERE"
)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

DEV_REDIRECT_URL = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "localhost")}/google_login/callback'  # noqa

print(
    f"""
=== Google OAuth Setup Instructions ===
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add this redirect URI: {DEV_REDIRECT_URL}
4. Add your Client ID and Secret to Replit Secrets:
   - GOOGLE_OAUTH_CLIENT_ID
   - GOOGLE_OAUTH_CLIENT_SECRET

For detailed setup: https://docs.replit.com/additional-resources/google-auth-in-flask # noqa
"""
)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    """Initiate Google OAuth login"""
    if GOOGLE_CLIENT_ID == "YOUR_GOOGLE_CLIENT_ID_HERE":
        flash(
            "Google OAuth is not configured. Please check the setup instructions.",  # noqa
            "error",
        )
        return redirect(url_for("main.index"))

    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url.replace("http://", "https://")
            + "/callback",  # noqa
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:  # noqa
        flash("Failed to initiate Google login. Please try again.", "error")
        return redirect(url_for("main.index"))


@google_auth.route("/google_login/callback")
def callback():
    """Handle Google OAuth callback"""
    try:
        code = request.args.get("code")
        if not code:
            flash("Google authentication was cancelled.", "warning")
            return redirect(url_for("main.index"))

        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=request.base_url.replace("http://", "https://"),
            code=code,
        )

        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        client.parse_request_body_response(json.dumps(token_response.json()))

        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        userinfo = userinfo_response.json()

        if not userinfo.get("email_verified"):
            flash(
                "Google account email not verified. Please verify your email with Google.",  # noqa
                "error",
            )
            return redirect(url_for("main.index"))

        users_email = userinfo["email"]
        users_first_name = userinfo.get("given_name", "")
        users_last_name = userinfo.get("family_name", "")
        profile_picture = userinfo.get("picture", "")

        # Check if user exists
        user = User.query.filter_by(email=users_email).first()

        if not user:
            # Create new user
            user = User()
            user.id = str(uuid.uuid4())
            user.email = users_email
            user.first_name = users_first_name
            user.last_name = users_last_name
            user.profile_image_url = profile_picture
            user.auth_type = "google"
            user.is_email_verified = True
            db.session.add(user)
            db.session.commit()
            flash(
                f"Welcome {users_first_name}! Your account has been created.",
                "success",
            )
        else:
            if user.auth_type in ["google"]:
                user.first_name = users_first_name or user.first_name
                user.last_name = users_last_name or user.last_name
                user.profile_image_url = (
                    profile_picture or user.profile_image_url
                )
                user.is_email_verified = True
                db.session.commit()
            flash(f"Welcome back, {user.first_name}!", "success")

        login_user(user)
        return redirect(url_for("main.workspace"))

    except Exception as e:  # noqa
        flash("Google authentication failed. Please try again.", "error")
        return redirect(url_for("main.index"))
