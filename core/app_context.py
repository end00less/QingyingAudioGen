# app/core/app_context.py
from app.controllers.application_controller import ApplicationController
from app.db.database import get_db


class AppContext:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            db_session = next(get_db())
            cls._instance = ApplicationController(db_session)
        return cls._instance