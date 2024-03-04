"""
This class contains all the util functions which loads different config files.

"""
import json
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def load_configs():
    config_file_path = os.environ.get("CONFIG_FILE_LOCATION")
    configs = dict()
    if config_file_path:
        if os.path.exists(config_file_path):
            with open(config_file_path, "r") as config_file:
                configs = json.load(config_file)
        else:
            logger.error("Config path doesn't exists")
    else:
        logger.error("Missing CONFIG_FILE_LOCATION argument.")
    return configs


fah_configs = load_configs()
logging.debug(fah_configs)


def getENVValue(var):
    env_var_val = os.environ.get(var)
    return env_var_val


# azure AD secrets
azure_client_id = getENVValue(
    fah_configs["AZURE_AD_SETTINGS"]["AZURE_CLIENT_ID"])
azure_client_secret = getENVValue(
    fah_configs["AZURE_AD_SETTINGS"]["AZURE_CLIENT_SECRET"]
)
azure_tenant_id = getENVValue(
    fah_configs["AZURE_AD_SETTINGS"]["AZURE_TENANT_ID"])
