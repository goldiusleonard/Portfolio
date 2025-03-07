"""configuration DTOs"""

from typing import List, Any, Union


class LoggingConfig:
    """Logging configuration class to be consumed by log manager"""

    def __init__(
        self, service_name: str, targets: List["TargetConfig"], rules: List["LogRule"]
    ):
        self.service_name = service_name
        targets = [
            target_config.with_service_name(service_name) for target_config in targets
        ]  # Pass service_name to each target config
        self.targets = targets
        self.rules = rules


class TargetConfig:
    """Base class for logging target configurations"""

    def __init__(
        self,
        name: str,
        target_type: str,
        #  level: str,
        pattern: Union[str, None],
        **kwargs: Any,
    ):
        self.name: str = name
        self.type: str = target_type
        # self.level = level
        self.format: Union[str, None] = pattern
        self.additional_params = kwargs  # Store additional parameters dynamically
        self.service_name: Union[str, None] = (
            None  # Placeholder for service_name, added in Derived classes
        )

    def with_service_name(self, service_name: Union[str, None]):
        """Method to inject service_name into the target configuration."""
        self.service_name = service_name
        return self


class ConsoleTargetConfig(TargetConfig):
    """Configuration class for Console logging"""

    def __init__(
        self,
        #  level: str,
        name: str,
        pattern: str,
    ):  # Changed 'format' to 'pattern'
        # self.level = level
        super().__init__(name=name, target_type="console", pattern=pattern)
        self.name = name
        self.pattern = pattern


class FileTargetConfig(TargetConfig):
    """Configuration class for File logging"""

    def __init__(
        self,
        #  level: str,
        name: str,
        path: str,
        size_limit: str,
        retention_count: int,
        #  rotation_duration: str,
        pattern: str,
    ):  # Updated parameter names
        # self.level = level
        super().__init__(name=name, target_type="file", pattern=pattern)
        self.name = name
        self.path = path
        self.size_limit = size_limit
        self.retention_count = retention_count
        # self.rotation_duration = rotation_duration
        self.pattern = pattern


class DatabaseTargetConfig(TargetConfig):
    """Configuration class for Database logging"""

    def __init__(
        self,
        #  level: str,
        name: str,
        protocol: str,
        hostname: str,
        port: int,
        username: str,
        password: str,
        database: str,
        # conn_string: str,
        table_name: str,
        columns: dict,
    ):  # Updated parameter names
        # self.level = level
        super().__init__(name=name, target_type="database", pattern=None)
        self.name = name
        self.protocol = protocol
        self.table_name = table_name
        self.columns = columns
        self.conn_string = (
            f"{protocol}://{username}:{password}@{hostname}:{port}/{database}"
        )


class EmailTargetConfig(TargetConfig):
    """Configuration class for Email logging"""

    def __init__(self, name: str, smtp: str, username: str, password: str):
        super().__init__(name=name, target_type="email", pattern=None)
        self.name = name
        self.smtp = smtp
        self.username = username
        self.password = password


class LogRule:
    """Class for rule configurations"""

    def __init__(
        self, name: str, logger: str, min_level: str, target: str, enabled: bool = True
    ):
        self.name = name
        self.logger = logger
        self.min_level = min_level
        self.target = target
        self.enabled = enabled
