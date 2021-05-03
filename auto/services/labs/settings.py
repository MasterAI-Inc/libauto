import os
import json


SETTINGS_PATH = os.environ.get('MAI_LABS_SETTINGS_PATH', '/var/lib/libauto/labs_settings.dict')


def load_settings():
    try:
        with open(SETTINGS_PATH, 'rt') as f:
            curr_settings = json.loads(f.read())
            return curr_settings
    except:
        # Something went wrong, don't care what...
        return {}


def save_settings(settings):
    """
    Saves the settings.
    Returns True if the settings *changed*.
    Returns False if the settings are the same.
    """
    curr_settings = load_settings()

    did_change = (curr_settings != settings)

    if did_change:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open (SETTINGS_PATH, 'wt') as f:
            f.write(json.dumps(settings))

    return did_change

