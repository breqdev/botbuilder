import os

from flask import Flask, redirect, url_for

import login
import dashboard


app = Flask(__name__)
app.secret_key = os.environ["DISCORD_CLIENT_SECRET"]

app.register_blueprint(login.bp, url_prefix="/login")
app.register_blueprint(dashboard.bp, url_prefix="/dashboard")


@app.route("/")
def index():
    return redirect(url_for("login.index"))


if __name__ == '__main__':
    app.run()
