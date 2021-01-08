import os

from flask import (Blueprint, session, render_template, request, current_app,
                   send_file, Response)

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

    user_directory = os.path.join(
        current_app.config["UPLOAD_FOLDER"], user["id"])

    if not os.path.exists(user_directory):
        os.mkdir(user_directory)

    # Save project workspace

    if "workspace" not in request.files:
        return "No selected file", 400

    workspace = request.files['workspace']

    if not workspace or workspace.filename == '':
        return "No selected file", 400

    workspace.save(os.path.join(user_directory, "workspace.xml"))

    # Save project code

    commands = request.files.getlist("command")

    for command in commands:
        if not command.filename.endswith(".js"):
            continue
        command.save(os.path.join(user_directory, command.filename))

    return "", 200


@bp.route("/load")
def load():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get("https://discord.com/api/v8/users/@me").json()

    user_directory = os.path.join(
        current_app.config["UPLOAD_FOLDER"], user["id"])

    filename = os.path.join(user_directory, "workspace.xml")

    if not os.path.exists(filename):
        # Nothing, return an empty workspace
        empty_workspace = \
            "<xml xmlns=\"https://developers.google.com/blockly/xml\"></xml>"
        return Response(empty_workspace, mimetype="text/xml")

    return send_file(filename)
