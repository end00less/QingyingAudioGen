# app/controllers/application_controller.py
from sqlalchemy.orm import Session

from app.controllers.project_controller import ProjectController
from app.controllers.chapter_controller import ChapterController
from app.controllers.line_controller import LineController
from app.controllers.role_controller import RoleController
from app.controllers.voice_controller import VoiceController
from app.controllers.emotion_controller import EmotionController
from app.controllers.strength_controller import StrengthController
from app.controllers.llm_provider_controller import LLMProviderController
from app.controllers.tts_provider_controller import TTSProviderController
from app.controllers.prompt_controller import PromptController
from app.controllers.multi_emotion_voice_controller import MultiEmotionVoiceController

from app.repositories.project_repository import ProjectRepository
from app.repositories.chapter_repository import ChapterRepository
from app.repositories.line_repository import LineRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.voice_repository import VoiceRepository
from app.repositories.emotion_repository import EmotionRepository
from app.repositories.strength_repository import StrengthRepository
from app.repositories.llm_provider_repository import LLMProviderRepository
from app.repositories.tts_provider_repository import TTSProviderRepository
from app.repositories.prompt_repository import PromptRepository
from app.repositories.multi_emotion_voice_repository import MultiEmotionVoiceRepository

from app.services.project_service import ProjectService
from app.services.chapter_service import ChapterService
from app.services.line_service import LineService
from app.services.role_service import RoleService
from app.services.voice_service import VoiceService
from app.services.emotion_service import EmotionService
from app.services.strength_service import StrengthService
from app.services.llm_provider_service import LLMProviderService
from app.services.tts_provider_service import TTSProviderService
from app.services.prompt_service import PromptService
from app.services.multi_emotion_voice_service import MultiEmotionVoiceService


class ApplicationController:
    """应用控制器管理器 - 统一管理所有控制器"""

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self._setup_controllers()

    def _setup_controllers(self):
        """设置所有控制器"""
        # 初始化Repository
        project_repo = ProjectRepository(self.db_session)
        chapter_repo = ChapterRepository(self.db_session)
        line_repo = LineRepository(self.db_session)
        role_repo = RoleRepository(self.db_session)
        voice_repo = VoiceRepository(self.db_session)
        emotion_repo = EmotionRepository(self.db_session)
        strength_repo = StrengthRepository(self.db_session)
        llm_provider_repo = LLMProviderRepository(self.db_session)
        tts_provider_repo = TTSProviderRepository(self.db_session)
        prompt_repo = PromptRepository(self.db_session)
        multi_emotion_voice_repo = MultiEmotionVoiceRepository(self.db_session)

        # 初始化Service
        project_service = ProjectService(project_repo)
        chapter_service = ChapterService(chapter_repo)
        line_service = LineService(line_repo, role_repo, tts_provider_repo)
        role_service = RoleService(role_repo)
        voice_service = VoiceService(voice_repo, multi_emotion_voice_repo)
        emotion_service = EmotionService(emotion_repo)
        strength_service = StrengthService(strength_repo)
        llm_provider_service = LLMProviderService(llm_provider_repo)
        tts_provider_service = TTSProviderService(tts_provider_repo)
        prompt_service = PromptService(prompt_repo)
        multi_emotion_voice_service = MultiEmotionVoiceService(multi_emotion_voice_repo)

        # 初始化Controller - 修改项目控制器初始化
        self.project_controller = ProjectController(
            project_service=project_service,
            chapter_service=chapter_service,
            role_service=role_service,
            llm_provider_service=llm_provider_service,  # 新增
            tts_provider_service=tts_provider_service  # 新增
        )

        self.chapter_controller = ChapterController(
            chapter_service, project_service, line_service, role_service,
            emotion_service, strength_service, prompt_service, voice_service
        )
        self.line_controller = LineController(
            line_service, project_service, chapter_service, role_service
        )
        self.role_controller = RoleController(
            role_service, project_service, line_service
        )
        self.voice_controller = VoiceController(
            voice_service, tts_provider_service
        )
        self.emotion_controller = EmotionController(emotion_service)
        self.strength_controller = StrengthController(strength_service)
        self.llm_provider_controller = LLMProviderController(llm_provider_service)
        self.tts_provider_controller = TTSProviderController(tts_provider_service)
        self.prompt_controller = PromptController(prompt_service)
        self.multi_emotion_voice_controller = MultiEmotionVoiceController(
            multi_emotion_voice_service, voice_service, emotion_service, strength_service
        )

    def close(self):
        """关闭数据库连接"""
        if self.db_session:
            self.db_session.close()