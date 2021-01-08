import os

from flask import (Blueprint, session, render_template, request, current_app,
                   send_file)

from login import make_session


bp = Blueprint(__name__, "dashboard")


@bp.route("/")
def index():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get("https://discord.com/api/v8/users/@me").json()
    return render_template("dashboard.html", user=user)


@bp.route('/save', methods=['POST'])
def save():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get("https://discord.com/api/v8/users/@me").json()

    if "file" not in request.files:
        return "No selected file", 400

    file = request.files['file']

    if file.filename == '':
        return "No selected file", 400

    if file:
        filename = f"{user['id']}.xml"

    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
    return "", 200


@bp.route("/load")
def load():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get("https://discord.com/api/v8/users/@me").json()

    filename = os.path.join(
        current_app.config["UPLOAD_FOLDER"], f"{user['id']}.xml")

    if not os.path.exists(filename):
        return "File not found", 400

    return send_file(filename)
