import os
from py_mini_racer import py_mini_racer
from flask import Blueprint, current_app


def run_command(user_id, command_name):
    command_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"], user_id, f"{command_name}.js")

    with open(command_path) as f:
        command_fn = f.read()

    print(command_fn)

    ctx = py_mini_racer.MiniRacer()

    ctx.eval("var command = " + command_fn)
    return_value = ctx.call("command")
    return return_value


bp = Blueprint(__name__, "interactions")


@bp.route("/interactions")
def interactions():
    return run_command("386352037723635712", "ping")
