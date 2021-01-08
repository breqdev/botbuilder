import os

from flask import (Blueprint, session, render_template, request, current_app,
                   send_file, Response)

from login import make_session
import redis

from commands_update import register_command, delete_commands

db = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)

bp = Blueprint(__name__, "dashboard")


@bp.route("/")
def index():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get("https://discord.com/api/v8/users/@me").json()
    return render_template(
        "dashboard.html", user=user, client_id=os.environ['DISCORD_CLIENT_ID'])


@bp.route('/save', methods=['POST'])
def save():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get("https://discord.com/api/v8/users/@me").json()

    user_directory = os.path.join(
        current_app.config["UPLOAD_FOLDER"], user["id"])

    if not os.path.exists(user_directory):
        os.mkdir(user_directory)

    # Update guilds mapping

    unfiltered_guilds = discord.get(
        "https://discord.com/api/v8/users/@me/guilds").json()

    guilds = []
    for guild in unfiltered_guilds:
        if int(guild["permissions"]) & 0x00000028:  # MANAGE_GUILD or ADMIN
            db.sadd(f"guild:{guild['id']}:users", user["id"])
            guilds.append(guild)

    # Save project workspace

    if "workspace" not in request.files:
        return "No selected file", 400

    workspace = request.files['workspace']

    if not workspace or workspace.filename == '':
        return "No selected file", 400

    workspace.save(os.path.join(user_directory, "workspace.xml"))

    # Delete existing commands

    for guild in guilds:
        delete_commands(
            guild["id"], db.smembers(f"user:{user['id']}:commands"))

    db.delete(f"user:{user['id']}:commands")

    for file in os.listdir(user_directory):
        if file.endswith(".js"):
            os.remove(os.path.join(user_directory, file))

    # Add new commands and code

    commands = request.files.getlist("command")

    for command in commands:
        if not command.filename.endswith(".js"):
            continue
        command.save(os.path.join(user_directory, command.filename))

        db.sadd(f"user:{user['id']}:commands", command.filename[:-3])

        for guild in guilds:
            register_command(guild["id"], command.filename[:-3])

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
