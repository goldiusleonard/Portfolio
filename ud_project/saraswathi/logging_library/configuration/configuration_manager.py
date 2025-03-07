import yaml
import urllib.parse

from .decrypt import decrypt
# from decrypt import decrypt
# import decrypt


class DatabaseConfiguration:
    """Class to represent database configuration."""

    def __init__(
        self,
        protocol: str,
        host: str,
        port: int,
        username: str,
        password: str,
        database_name: str,
        config_name: str,
    ):
        self.protocol = protocol
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database_name = database_name
        self.config_name = config_name

    def get_connection_string(self):
        """return connection string from the configuration"""
        username = urllib.parse.quote_plus(self.username)
        decrypted_password = decrypt(self.password)
        password = urllib.parse.quote_plus(decrypted_password)
        connection_string = f"{self.protocol}://"
        connection_string += f"{username}:{password}"
        connection_string += f"@{self.host}:{self.port}"
        connection_string += f"/{self.database_name}"
        return connection_string


class ConfigurationManager:
    """Configuration manager that loads configurations from a YAML file."""

    database_configurations: dict = {}
    app_settings: dict = {}
    __initialized__: bool = False

    @classmethod
    def initialize(cls):
        """Dynamically load configuration from YAML and populate the class attributes."""
        if cls.__initialized__:
            print("Configuration already initialized.")
            return  # Prevent re-initialization

        try:
            print("Loading YAML configuration...")
            # Load the YAML configuration file
            with open("logging_library/app_config.yaml", "r", encoding="UTF-8") as file:
                config = yaml.safe_load(file)
                print("YAML loaded successfully")

            # Populate database configurations as a dictionary (config_name as key)
            if "database" in config:
                cls.database_configurations = {
                    db_config["config_name"]: DatabaseConfiguration(
                        **{**db_config, "config_name": db_config["config_name"]}
                    )
                    for db_config in config["database"]
                }
                print(f"Database configurations loaded: {cls.database_configurations}")

            # Populate app settings
            if "app_settings" in config:
                cls.app_settings = config["app_settings"]
                print(f"App settings loaded: {cls.app_settings}")

            # Mark the class as initialized
            cls.__initialized__ = True
            print("Configuration initialized successfully.")

        except FileNotFoundError:
            print("Configuration file not found!")
            raise
        except yaml.YAMLError as e:
            print(f"Error reading YAML file: {e}")
            raise


ConfigurationManager.initialize()
