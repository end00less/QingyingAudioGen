# app/controllers/voice_controller.py
from typing import List, Optional

from app.controllers.base_controller import BaseController, BusinessException
from app.entity.voice_entity import VoiceEntity
from app.services.voice_service import VoiceService
from app.services.tts_provider_service import TTSProviderService


class VoiceController(BaseController):
    def __init__(self,
                 voice_service: VoiceService,
                 tts_provider_service: TTSProviderService):
        self.voice_service = voice_service
        self.tts_provider_service = tts_provider_service

    def create_voice(self, tts_provider_id: int, name: str,
                     reference_path: str = None, description: str = None,
                     is_multi_emotion: int = 0) -> VoiceEntity:
        """创建音色"""
        tts_provider = self.tts_provider_service.get_tts_provider(tts_provider_id)
        if not tts_provider:
            raise BusinessException(f"TTS服务商 {tts_provider_id} 不存在")

        entity = VoiceEntity(
            tts_provider_id=tts_provider_id,
            name=name,
            reference_path=reference_path,
            description=description,
            is_multi_emotion=is_multi_emotion
        )

        result = self.voice_service.create_voice(entity)
        if result is None:
            raise BusinessException(f"音色 '{name}' 已存在")
        return result

    def get_voice(self, voice_id: int) -> VoiceEntity:
        """根据ID查询音色"""
        entity = self.voice_service.get_voice(voice_id)
        if not entity:
            raise BusinessException(f"音色 {voice_id} 不存在", 404)
        return entity

    def get_voices_by_tts_provider(self, tts_provider_id: int) -> List[VoiceEntity]:
        """获取TTS服务商下所有音色"""
        tts_provider = self.tts_provider_service.get_tts_provider(tts_provider_id)
        if not tts_provider:
            raise BusinessException(f"TTS服务商 {tts_provider_id} 不存在")
        return self.voice_service.get_all_voices(tts_provider_id)

    def update_voice(self, voice_id: int, **kwargs) -> bool:
        """更新音色"""
        voice = self.get_voice(voice_id)
        if not voice:
            raise BusinessException("音色不存在")

        success = self.voice_service.update_voice(voice_id, kwargs)
        if not success:
            raise BusinessException("更新失败，音色名称可能已存在或TTS服务商ID被修改")
        return success

    def delete_voice(self, voice_id: int) -> bool:
        """删除音色"""
        voice = self.get_voice(voice_id)
        if not voice:
            raise BusinessException("音色不存在")

        success = self.voice_service.delete_voice(voice_id)
        if not success:
            raise BusinessException("删除失败")
        return success

    def initialize_default_voices(self, tts_provider_id: int) -> bool:
        """初始化默认音色库"""
        try:
            # 验证TTS服务商是否存在
            tts_provider = self.tts_provider_service.get_tts_provider(tts_provider_id)
            if not tts_provider:
                raise BusinessException(f"TTS服务商 {tts_provider_id} 不存在")

            return self.voice_service.initialize_default_voices(tts_provider_id)

        except Exception as e:
            print(f"初始化默认音色失败: {e}")
            return False