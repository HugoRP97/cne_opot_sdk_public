import os
from configparser import BasicInterpolation, ConfigParser
import connexion
import logging
# For error validators
from opot_sdk.opot_controller.OPoTController import OPoTController

# Setup the config

#  We must consider that here the values from the .ini file have .ini values are predominant over environment variables
class EnvInterpolation(BasicInterpolation):
    """Interpolation which expands environment variables in values."""

    def before_get(self, parser, section, option, value, defaults):
        value = super().before_get(parser, section, option, value, defaults)
        return os.path.expandvars(value)

def instantiate_api():
    # Setting up the configuration of the API
    parser = ConfigParser(os.environ, interpolation=EnvInterpolation())
    parser.read("/etc/default/controller_config.ini")
    api = parser['OPENAPI']
    # OpenAPI IP Address
    api_ip = api['OPEN_API_IP']
    # OpenAPI Port
    api_port = int(api.get("OPEN_API_PORT", 8080))

    # Setup logging module for API
    logger = logging.getLogger("connexion.decorators.validation")

    # Instantiating the API
    app = connexion.App("__name__", specification_dir=f'{os.path.dirname(__file__)}/../config/api')
    # Adding the OPENAPI template
    app.add_api('./openapi.v1.yaml')
    # Running the application
    app.run(host=api_ip, port=api_port)
    # Starting the Controller
    OPoTController().start()
    application = app.app

if __name__ == '__main__':
   instantiate_api()
