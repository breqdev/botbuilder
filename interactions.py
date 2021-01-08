import os
from py_mini_racer import py_mini_racer
from flask import Blueprint, current_app
import redis

db = redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def run_user_command(user_id, command_name):
    command_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"], user_id, f"{command_name}.js")

    if not os.path.exists(command_path):
        return "Command Not Found", 404

    with open(command_path) as f:
        command_fn = f.read()

    ctx = py_mini_racer.MiniRacer()

    javascript = "function command() {\n" + command_fn + "\n}"

    ctx.eval(javascript)
    return_value = ctx.call("command")
    return return_value


def run_command(guild_id, command_name):
    users = db.smembers(f"guild:{guild_id}:users")

    for user_id in users:
        if db.sismember(f"user:{user_id}:commands", command_name):
            break
    else:
        return "User Not Found", 404

    return run_user_command(user_id, command_name)


bp = Blueprint(__name__, "interactions")


@bp.route("/interactions")
def interactions():
    return run_command("748012955404337296", "ping") or ""
