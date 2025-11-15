# app/controllers/multi_emotion_voice_controller.py
from typing import List, Optional, Dict

from app.controllers.base_controller import BaseController, BusinessException
from app.entity.multi_emotion_voice_entity import MultiEmotionVoiceEntity
from app.services.multi_emotion_voice_service import MultiEmotionVoiceService
from app.services.voice_service import VoiceService
from app.services.emotion_service import EmotionService
from app.services.strength_service import StrengthService


class MultiEmotionVoiceController(BaseController):
    def __init__(self,
                 multi_emotion_voice_service: MultiEmotionVoiceService,
                 voice_service: VoiceService,
                 emotion_service: EmotionService,
                 strength_service: StrengthService):
        self.multi_emotion_voice_service = multi_emotion_voice_service
        self.voice_service = voice_service
        self.emotion_service = emotion_service
        self.strength_service = strength_service

    def create_multi_emotion_voice(self, voice_id: int, emotion_id: int,
                                   strength_id: int, reference_path: str = None) -> MultiEmotionVoiceEntity:
        """创建多情绪音色"""
        # 验证音色、情绪、强度是否存在
        voice = self.voice_service.get_voice(voice_id)
        emotion = self.emotion_service.get_emotion(emotion_id)
        strength = self.strength_service.get_strength(strength_id)

        if not voice or not emotion or not strength:
            raise BusinessException("音色、情绪或强度不存在")

        entity = MultiEmotionVoiceEntity(
            voice_id=voice_id,
            emotion_id=emotion_id,
            strength_id=strength_id,
            reference_path=reference_path
        )

        result = self.multi_emotion_voice_service.create_multi_emotion_voice(entity)
        if result is None:
            raise BusinessException("创建失败，该多情绪音色已存在")
        return result

    def get_multi_emotion_voice(self, multi_emotion_voice_id: int) -> MultiEmotionVoiceEntity:
        """根据ID查询多情绪音色"""
        entity = self.multi_emotion_voice_service.get_multi_emotion_voice_by_id(multi_emotion_voice_id)
        if not entity:
            raise BusinessException(f"多情绪音色 {multi_emotion_voice_id} 不存在", 404)
        return entity

    def get_multi_emotion_voice_by_combination(self, voice_id: int, emotion_id: int,
                                               strength_id: int) -> MultiEmotionVoiceEntity:
        """根据组合查询多情绪音色"""
        entity = self.multi_emotion_voice_service.get_multi_emotion_voice_by_voice_id_emotion_id_strength_id(
            voice_id, emotion_id, strength_id
        )
        if not entity:
            raise BusinessException("多情绪音色不存在", 404)
        return entity

    def get_multi_emotion_voices_by_voice(self, voice_id: int) -> List[MultiEmotionVoiceEntity]:
        """根据音色ID获取所有多情绪音色"""
        voice = self.voice_service.get_voice(voice_id)
        if not voice:
            raise BusinessException(f"音色 {voice_id} 不存在")
        return self.multi_emotion_voice_service.get_multi_emotion_voice_by_voice_id(voice_id)

    def get_all_multi_emotion_voices(self) -> List[MultiEmotionVoiceEntity]:
        """获取所有多情绪音色"""
        return self.multi_emotion_voice_service.get_all_multi_emotion_voices()

    def update_multi_emotion_voice(self, multi_emotion_voice_id: int, **kwargs) -> bool:
        """更新多情绪音色"""
        multi_emotion_voice = self.get_multi_emotion_voice(multi_emotion_voice_id)
        if not multi_emotion_voice:
            raise BusinessException("多情绪音色不存在")

        success = self.multi_emotion_voice_service.update_multi_emotion_voice(multi_emotion_voice_id, kwargs)
        if not success:
            raise BusinessException("更新失败")
        return success

    def delete_multi_emotion_voice(self, multi_emotion_voice_id: int) -> bool:
        """删除多情绪音色"""
        multi_emotion_voice = self.get_multi_emotion_voice(multi_emotion_voice_id)
        if not multi_emotion_voice:
            raise BusinessException("多情绪音色不存在")

        success = self.multi_emotion_voice_service.delete_multi_emotion_voice(multi_emotion_voice_id)
        if not success:
            raise BusinessException("删除失败")
        return success

    def delete_all_multi_emotion_voices_by_voice(self, voice_id: int) -> bool:
        """删除音色下所有多情绪音色"""
        voice = self.voice_service.get_voice(voice_id)
        if not voice:
            raise BusinessException(f"音色 {voice_id} 不存在")

        success = self.multi_emotion_voice_service.delete_multi_emotion_voice_by_voice_id(voice_id)
        if not success:
            raise BusinessException("删除失败")
        return success