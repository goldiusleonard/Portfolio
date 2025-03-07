import json
import os


def read_cookies():
    """
    Loads the config file and returns it.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "cookies.json")
    with open(config_path, "r") as f:
        return json.load(f)
