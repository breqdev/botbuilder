import os

from flask import Blueprint, session, request, redirect, url_for
from requests_oauthlib import OAuth2Session

OAUTH2_CLIENT_ID = os.environ["DISCORD_CLIENT_ID"]
OAUTH2_CLIENT_SECRET = os.environ["DISCORD_CLIENT_SECRET"]
OAUTH2_REDIRECT_URI = os.environ["DISCORD_REDIRECT_URL"]


bp = Blueprint(__name__, "login")

if 'http://' in OAUTH2_REDIRECT_URI:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url="https://discord.com/api/v8/oauth2/token",
        token_updater=token_updater)


@bp.route("/")
def index():
    discord = make_session(scope=["identify", "email"])
    authorization_url, state = discord.authorization_url(
        "https://discord.com/api/v8/oauth2/authorize")
    session['oauth2_state'] = state
    return redirect(authorization_url)


@bp.route("/callback")
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        "https://discord.com/api/v8/oauth2/token",
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    return redirect(url_for("dashboard.index"))
