# app/core/app_context.py
from app.controllers.application_controller import ApplicationController
from app.db.database import get_db
from app.services.audio_player_service import audio_player


class AppContext:
    def __init__(self):
        self._initialize_services()

    def _initialize_services(self):
        """初始化所有服务"""
        print("🚀 初始化应用服务...")

        # 音频播放器已经在导入时初始化了
        # 但我们这里可以验证一下
        print(f"🎵 音频播放器状态: {'就绪' if hasattr(audio_player, 'is_playing') else '未初始化'}")

        # 其他服务初始化...
        print("✅ 所有服务初始化完成")
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            db_session = next(get_db())
            cls._instance = ApplicationController(db_session)
        return cls._instance