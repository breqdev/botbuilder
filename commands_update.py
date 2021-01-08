import os
import time

import requests

OAUTH2_CLIENT_ID = os.environ["DISCORD_CLIENT_ID"]
OAUTH2_CLIENT_SECRET = os.environ["DISCORD_CLIENT_SECRET"]

own_token = None


def get_own_token():
    global own_token
    data = {
        "grant_type": "client_credentials",
        "scope": "applications.commands.update"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    r = requests.post(
        "https://discord.com/api/v8/oauth2/token",
        data=data, headers=headers,
        auth=(OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET)
    )
    r.raise_for_status()
    own_token = r.json()
    own_token["expires_on"] = (time.time() + own_token["expires_in"]/2)


def auth_headers():
    global own_token
    if (own_token is None or time.time() > own_token["expires_on"]):
        get_own_token()
    return {"Authorization": f"Bearer {own_token['access_token']}"}


def register_command(guild_id, command_name):
    url = ("https://discord.com/api/v8/applications/"
           f"{OAUTH2_CLIENT_ID}/"
           f"guilds/{guild_id}/commands")

    json = {
        "name": command_name,
        "description": "Made with <3 and BotBuilder by Breq",
        "options": []
    }

    response = requests.post(url, json=json, headers=auth_headers())

    if response.status_code == 403:
        return  # User hasn't granted permission for this guild, fail silently

    response.raise_for_status()


def delete_commands(guild_id, command_names):
    url = ("https://discord.com/api/v8/applications/"
           f"{OAUTH2_CLIENT_ID}/"
           f"guilds/{guild_id}/commands")

    response = requests.get(url, headers=auth_headers())

    if response.status_code == 403:
        return  # User hasn't granted permission for this guild, fail silently

    response.raise_for_status()
    all_commands = response.json()

    for command in all_commands:
        if command["name"] in command_names:
            response = requests.delete(
                url+"/"+command["id"], headers=auth_headers())
            response.raise_for_status()
