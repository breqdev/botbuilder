import os
from py_mini_racer import py_mini_racer
from flask import Blueprint, current_app, request, jsonify
import redis
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

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


def verify_signature(data, signature, timestamp):
    message = timestamp.encode() + data
    verify_key = VerifyKey(
        bytes.fromhex(os.environ["DISCORD_PUBLIC_KEY"]))
    try:
        verify_key.verify(message, bytes.fromhex(signature))
    except BadSignatureError:
        return False
    else:
        return True


bp = Blueprint(__name__, "interactions")


@bp.route("/interactions", methods=["POST"])
def interactions():
    signature = request.headers.get('X-Signature-Ed25519')
    timestamp = request.headers.get('X-Signature-Timestamp')

    if (signature is None or timestamp is None
            or not verify_signature(request.data, signature, timestamp)):
        return "Bad Request Signature", 401

    if (request.json and request.json.get("type") == 1):
        return jsonify({"type": 1})

    result = run_command(
        request.json["guild_id"], request.json["data"]["name"])

    return jsonify({
        "type": 4,
        "data": {
            "tts": False,
            "content": result,
            "embeds": [],
            "allowed_mentions": []
        }
    })
