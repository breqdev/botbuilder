import os
from botocore.exceptions import ClientError

from flask import Blueprint, session, render_template, request, Response

from login import make_session

from commands_update import overwrite_commands

from storage import s3, redis

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
            redis.sadd(f"guild:{guild['id']}:users", user["id"])
            guilds.append(guild)

    # Save project workspace

    if "workspace" not in request.files:
        return "No selected file", 400

    workspace = request.files['workspace']

    if not workspace or workspace.filename == '':
        return "No selected file", 400

    s3.put_object(
        Bucket=os.environ["S3_BUCKET"],
        Key=f"{user['id']}/workspace.xml",
        Body=workspace
    )

    # Get the difference between old and new commands

    current_commands = redis.smembers(f"user:{user['id']}:commands")
    updated_commands = [
        file.filename[:-3] for file in request.files.getlist("command")
        if file.filename.endswith(".js")
    ]

    if set(current_commands) != set(updated_commands):
        for guild in guilds:
            overwrite_commands(guild["id"], updated_commands)

    # Delete existing commands

    for command in redis.smembers(f"user:{user['id']}:commands"):
        try:
            s3.delete_object(
                Bucket=os.environ["S3_BUCKET"],
                Key=f"{user['id']}/{command}.js"
            )
        except ClientError:
            pass

    redis.delete(f"user:{user['id']}:commands")

    # Add new commands and code

    commands = request.files.getlist("command")

    for command in commands:
        if not command.filename.endswith(".js"):
            continue

        s3.put_object(
            Bucket=os.environ["S3_BUCKET"],
            Key=f"{user['id']}/{command.filename}",
            Body=command
        )

        redis.sadd(f"user:{user['id']}:commands", command.filename[:-3])

    return "", 200


@bp.route("/load")
def load():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get("https://discord.com/api/v8/users/@me").json()

    try:
        workspace = s3.get_object(
            Bucket=os.environ["S3_BUCKET"],
            Key=f"{user['id']}/workspace.xml"
        )["Body"].read()
    except ClientError:
        # Nothing, return an empty workspace
        empty_workspace = \
            "<xml xmlns=\"https://developers.google.com/blockly/xml\"></xml>"
        return Response(empty_workspace, mimetype="text/xml")
    else:
        return Response(workspace, mimetype="text/xml")
