"""This is the module to add performance logs"""

from typing import Optional, Union
import functools
import inspect
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .performance_log_dto import PerformanceLog
from ..configuration.configuration_manager import ConfigurationManager


class PerformanceLogger:
    """Class for defining methods to log performance metrics"""

    __performance_log__: Union[PerformanceLog, None] = None
    __start_time__: Union[datetime, None] = None
    __end_time__: Union[datetime, None] = None

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id

        stack = inspect.stack()
        self.caller_function = stack[1].function  # The function that called __enter__
        self.caller_module = stack[
            1
        ].filename  # The file from where the function is called
        self.caller_class = None

        self.service_name = ConfigurationManager.app_settings["service_name"]

        # If it's a class method, we can retrieve the class name
        if "self" in stack[1].frame.f_locals:
            self.caller_class = stack[1].frame.f_locals["self"].__class__.__name__

        self.__db_configuration__ = ConfigurationManager.database_configurations[
            "application_database"
        ]
        engine = create_engine(self.__db_configuration__.get_connection_string())

        self.db_session: Session = sessionmaker(bind=engine)()

    def log_performance(self, func):
        """method to be used as a decorator on functions which require logging"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # log start time
            result = func(*args, **kwargs)
            # log end time
            return result

        return wrapper

    def __enter__(self):
        self.__start_time__ = datetime.now()
        self.__log_start_time__()

    def __exit__(self, exc_type, exc_value, traceback):
        self.__end_time__ = datetime.now()
        self.__log_end_time__()

    def __log_start_time__(self):
        self.__performance_log__ = PerformanceLog(
            session_id=self.session_id,
            function_name=self.caller_function,
            class_name=self.caller_class,
            module_name=self.caller_module,
            start_time=self.__start_time__,
            service_name=self.service_name,
        )
        if self.db_session:
            self.db_session.add(self.__performance_log__)
            self.db_session.commit()  # Commit the transaction to save the log

    def __log_end_time__(self):
        # if duration is None:
        duration = (self.__end_time__ - self.__start_time__).total_seconds()
        if self.__performance_log__:
            self.__performance_log__.end_time = self.__end_time__
            self.__performance_log__.duration = duration

        # Commit the update to the database
        if self.db_session:
            self.db_session.commit()  # Commit the update transaction
