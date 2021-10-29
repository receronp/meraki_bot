# settings.py
from os import environ
import meraki


def init():
    global dashboard
    global networkId
    global bot_env
    # BASE_URL = "http://api.meraki.com/api/v1/"
    MERAKI_API_KEY = environ.get("MERAKI_API_KEY")
    dashboard = meraki.DashboardAPI(
        MERAKI_API_KEY, print_console=False, output_log=False
    )

    # Retrieve required details from environment variables
    bot_env = {
        "BOT_APP_NAME": environ.get("TEAMS_BOT_APP_NAME"),
        "BOT_TOKEN": environ.get("TEAMS_BOT_TOKEN"),
        "BOT_URL": environ.get("TEAMS_BOT_URL"),
        "BOT_EMAIL": environ.get("TEAMS_BOT_EMAIL"),
    }
