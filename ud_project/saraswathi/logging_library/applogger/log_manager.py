"""Log manager module"""

import datetime
import logging
import urllib.parse
import os
from typing import Optional
from logging.handlers import TimedRotatingFileHandler
from sqlalchemy import (
    create_engine,
    Table,
    Column,
    MetaData,
    String,
    Text,
    DateTime,
    insert,
    BigInteger,
)
import yaml

from ..configuration.configuration_manager import ConfigurationManager
from ..configuration.log_configuration import (
    DatabaseTargetConfig,
    LoggingConfig,
    ConsoleTargetConfig,
    FileTargetConfig,
    LogRule,
)
from ..configuration.decrypt import decrypt


class LogManager:
    """Wrapper class for logging"""

    def __init__(self, session_id: Optional[str] = None):
        self.config = self._load_config()
        self.logger = self._setup_logger()  # Default logger
        self.loggers: dict = {}  # Dictionary to store loggers by name
        self.session_id = session_id
        self._setup_loggers()  # Setup loggers based on rules

    def _load_config(self) -> LoggingConfig:
        # Load the configuration from the YAML file

        # Get the current file's directory
        current_directory = os.path.dirname(__file__)
        # Construct the path to the base directory
        base_directory = os.path.abspath(os.path.join(current_directory, ".."))

        config_file_path = os.path.join(base_directory, "log_config.yaml")

        if not os.path.exists(config_file_path):
            raise FileNotFoundError("the configuration file does not exist")

        with open(config_file_path, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)

        # Create targets
        targets: list = []
        for target in config_data["logging"]["targets"]:
            target_name = target.get("name", None)

            if target_name is None:
                raise RuntimeError("Target name is not available!")

            target_type = target.get("type", None)

            if target_type is None:
                raise RuntimeError("Target type is not available!")

            if target_type == "console":
                target_pattern = target.get("pattern", None)

                if target_pattern is None:
                    raise RuntimeError("Target pattern is not available!")

                targets.append(
                    ConsoleTargetConfig(name=target_name, pattern=target_pattern)
                )  # Pass only necessary args
            elif target_type == "file":
                targets.append(
                    FileTargetConfig(
                        name=target["name"],
                        path=target["path"],
                        size_limit=target["size_limit"],
                        retention_count=target["retention_count"],
                        # rotation_duration=target['rotation_duration'],
                        pattern=target["pattern"],
                    )
                )  # Pass only necessary args
            elif target_type == "database":
                db_config = ConfigurationManager.database_configurations[
                    target["database_configuration"]
                ]
                decrypted_password = decrypt(db_config.password)
                targets.append(
                    DatabaseTargetConfig(
                        name=target.get("name", ""),
                        protocol=db_config.protocol,
                        hostname=db_config.host,
                        port=db_config.port,
                        username=db_config.username,
                        password=urllib.parse.quote_plus(decrypted_password),
                        database=db_config.database_name,
                        table_name=target["table_name"],
                        columns=target["columns"],
                    )
                )
            elif target_type == "email":
                raise NotImplementedError("Email Logging is not implemented!")
            else:
                print(
                    f"Unknown target type: {target_type}"
                )  # Error handling for unknown types
                raise ValueError(f"Unknown target type: {target_type}")

        # Create rules
        rules = [LogRule(**rule) for rule in config_data["logging"]["rules"]]

        # Create the logging configuration object
        return LoggingConfig(
            service_name=ConfigurationManager.app_settings["service_name"],
            targets=targets,
            rules=rules,
        )

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(self.config.service_name)
        logger.setLevel(logging.DEBUG)

        # Setup all targets
        for target in self.config.targets:
            if isinstance(target, ConsoleTargetConfig):
                logging_stream_handler = logging.StreamHandler()
                logging_stream_handler.setLevel(logging.DEBUG)
                logging_stream_handler.setFormatter(logging.Formatter(target.pattern))
                logger.addHandler(logging_stream_handler)

            elif isinstance(target, FileTargetConfig):
                time_rotating_file_handler = TimedRotatingFileHandler(
                    target.path, when="midnight", backupCount=target.retention_count
                )
                time_rotating_file_handler.setLevel(logging.DEBUG)
                time_rotating_file_handler.setFormatter(
                    logging.Formatter(target.pattern)
                )
                logger.addHandler(time_rotating_file_handler)

            elif isinstance(target, DatabaseTargetConfig):
                database_handler = DatabaseHandler(target)
                logger.addHandler(database_handler)

        return logger

    def _setup_loggers(self) -> None:
        # Set up additional loggers based on rules defined in the config
        for rule in self.config.rules:
            if not rule.enabled:
                continue
            logger = logging.getLogger(rule.name)
            logger.setLevel(rule.min_level)

            rule_target_name = rule.target
            # Map the rule's target to the appropriate target config object
            target = next(
                (t for t in self.config.targets if t.name == rule_target_name), None
            )

            # Set up the handler for the logger based on the target
            if target:
                if isinstance(target, ConsoleTargetConfig):
                    logging_stream_handler = logging.StreamHandler()
                    logging_stream_handler.setFormatter(
                        logging.Formatter(target.pattern)
                    )
                    logger.addHandler(logging_stream_handler)

                elif isinstance(target, FileTargetConfig):
                    time_rotating_file_handler = TimedRotatingFileHandler(
                        target.path, when="midnight", backupCount=target.retention_count
                    )
                    time_rotating_file_handler.setFormatter(
                        logging.Formatter(target.pattern)
                    )
                    logger.addHandler(time_rotating_file_handler)

                elif isinstance(target, DatabaseTargetConfig):
                    database_handler = DatabaseHandler(
                        target, session_id=self.session_id
                    )
                    logger.addHandler(database_handler)

            self.loggers[rule.name] = logger  # Store logger by name

    def get_logger(self) -> logging.Logger:
        """return the current logger object"""
        return self.logger

    def get_logger_by_name(self, name: str) -> logging.Logger:
        """return the logger object by name"""
        if name in self.loggers:
            return self.loggers[name]
        else:
            raise ValueError(f"No logger found with the name: {name}")


class DatabaseHandler(logging.Handler):
    """Database log handler"""

    def __init__(self, config: DatabaseTargetConfig, session_id: Optional[str] = None):
        logging.Handler.__init__(self)
        self.table_name = config.table_name
        self.columns = config.columns
        self.service_name = config.service_name
        self.session_id = session_id

        # Create a DB connection engine
        self.engine = create_engine(config.conn_string)
        self.connection = self.engine.connect()

        # Define the logs table using the column names from config
        self.metadata = MetaData()
        self.logs_table = Table(
            self.table_name,
            self.metadata,
            Column(
                "id", BigInteger, primary_key=True, autoincrement=True
            ),  # Add ID field
            *[
                Column(col_name, self._get_column_type(col_type))
                for col_name, col_type in self.columns.items()
            ],
            autoload_with=self.engine,
        )
        self.metadata.create_all(self.engine)

    def _get_column_type(self, col_type):
        """Map string column types to SQLAlchemy column types."""
        col_type_map = {
            "varchar": String,
            "text": Text,
            "datetime": DateTime,
            "bigint": BigInteger,
        }
        # Extract the base type (in case of varchar with length)
        if "(" in col_type["datatype"]:
            base_type, length = col_type["datatype"].split("(")
            length = int(length.strip(")"))
            return col_type_map[base_type](length)
        return col_type_map[col_type["datatype"]]()

    def emit(self, record: logging.LogRecord) -> None:
        # Create a log entry dictionary based on the configuration
        log_entry: dict = {}
        # Populate log entry based on columns specified in the config
        for column_name, column_config in self.columns.items():
            value_type = column_config.get("value_type", None)
            if value_type == "loglevel":
                # Get the log level
                log_entry[column_name] = record.levelname
            elif value_type == "session_id":
                # Get the session/request id
                log_entry[column_name] = self.session_id
            elif value_type == "logdate":
                # For timestamp fields
                log_entry[column_name] = datetime.datetime.now()
            elif value_type == "message":
                # Get message for text fields
                log_entry[column_name] = record.getMessage()
            elif value_type == "calling_method":
                # Get the function name
                log_entry[column_name] = record.funcName
            elif value_type == "calling_module":
                # Get the module name
                log_entry[column_name] = record.module
            elif value_type == "application_name":
                # Get the application/service name
                log_entry[column_name] = self.service_name
            else:
                # Use getattr to fetch other attributes directly from the log record
                log_entry[column_name] = getattr(record, column_name, "None")
        try:
            self.connection.execute(insert(self.logs_table).values(log_entry))
            self.connection.commit()
        except Exception:
            self.connection.rollback()
