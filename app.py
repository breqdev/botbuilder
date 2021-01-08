import os

from flask import Flask, render_template, session, redirect, url_for

import login
import dashboard
import interactions


app = Flask(__name__)
app.secret_key = os.environ["DISCORD_CLIENT_SECRET"]
app.config["UPLOAD_FOLDER"] = os.environ["UPLOAD_FOLDER"]

app.register_blueprint(login.bp, url_prefix="/login")
app.register_blueprint(dashboard.bp, url_prefix="/dashboard")
app.register_blueprint(interactions.bp)


@app.route("/")
def index():
    if "oauth2_token" in session:
        return redirect(url_for("dashboard.index"))
    return render_template("index.html")


if __name__ == '__main__':
    app.run()
