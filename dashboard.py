import os

from flask import Blueprint, session, render_template, request, Response

from login import make_session
import redis
import minio

from commands_update import register_command, delete_commands

db = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)
storage = minio.Minio(
    os.environ["MINIO_ENDPOINT"],
    access_key=os.environ["MINIO_ACCESS_KEY"],
    secret_key=os.environ["MINIO_SECRET_KEY"]
)

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

    size = os.fstat(workspace.fileno()).st_size

    storage.put_object("botbuilder", f"{user['id']}/workspace.xml", workspace, size)

    # Delete existing commands

    for guild in guilds:
        delete_commands(
            guild["id"], db.smembers(f"user:{user['id']}:commands"))

    for command in db.smembers(f"user:{user['id']}:commands"):
        storage.remove_object("botbuilder", f"{user['id']}/{command}.js")

    db.delete(f"user:{user['id']}:commands")

    # Add new commands and code

    commands = request.files.getlist("command")

    for command in commands:
        if not command.filename.endswith(".js"):
            continue

        size = os.fstat(command.fileno()).st_size
        storage.put_object("botbuilder", f"{user['id']}/{command.filename}", command, size)

        db.sadd(f"user:{user['id']}:commands", command.filename[:-3])

        for guild in guilds:
            register_command(guild["id"], command.filename[:-3])

    return "", 200


@bp.route("/load")
def load():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get("https://discord.com/api/v8/users/@me").json()

    try:
        workspace = storage.get_object("botbuilder", f"{user['id']}/workspace.xml")
    except minio.error.S3Error:
        # Nothing, return an empty workspace
        empty_workspace = \
            "<xml xmlns=\"https://developers.google.com/blockly/xml\"></xml>"
        return Response(empty_workspace, mimetype="text/xml")
    else:
        return Response(workspace, mimetype="text/xml")
