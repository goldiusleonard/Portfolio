"""module to define ORM for performance log table(s)"""

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from typing import Annotated

Base: Annotated[type, "SQLAlchemy ORM base"] = declarative_base()


class PerformanceLog(Base):
    """PerformanceLog DTO"""

    __tablename__ = "performance_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, nullable=False)
    function_name = Column(String, nullable=False)
    # caller_function_name = Column(String, nullable=False)
    class_name = Column(String, nullable=True)
    module_name = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    duration = Column(Float, nullable=False)
    service_name = Column(String, nullable=True)
