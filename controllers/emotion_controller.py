# app/controllers/emotion_controller.py
from typing import List, Optional

from app.controllers.base_controller import BaseController, BusinessException
from app.entity.emotion_entity import EmotionEntity
from app.services.emotion_service import EmotionService


class EmotionController(BaseController):
    def __init__(self, emotion_service: EmotionService):
        self.emotion_service = emotion_service

    def create_emotion(self, name: str, description: str = None) -> EmotionEntity:
        """创建情绪"""
        entity = EmotionEntity(name=name, description=description)

        result = self.emotion_service.create_emotion(entity)
        if result is None:
            raise BusinessException(f"情绪 '{name}' 已存在")
        return result

    def get_emotion(self, emotion_id: int) -> EmotionEntity:
        """根据ID查询情绪"""
        entity = self.emotion_service.get_emotion(emotion_id)
        if not entity:
            raise BusinessException(f"情绪 {emotion_id} 不存在", 404)
        return entity

    def get_emotion_by_name(self, name: str) -> EmotionEntity:
        """根据名称查询情绪"""
        entity = self.emotion_service.get_emotion_by_name(name)
        if not entity:
            raise BusinessException(f"情绪 '{name}' 不存在", 404)
        return entity

    def get_all_emotions(self) -> List[EmotionEntity]:
        """获取所有情绪"""
        return self.emotion_service.get_all_emotions()

    def update_emotion(self, emotion_id: int, **kwargs) -> bool:
        """更新情绪"""
        emotion = self.get_emotion(emotion_id)
        if not emotion:
            raise BusinessException("情绪不存在")

        success = self.emotion_service.update_emotion(emotion_id, kwargs)
        if not success:
            raise BusinessException("更新失败，情绪名称可能已存在")
        return success

    def delete_emotion(self, emotion_id: int) -> bool:
        """删除情绪"""
        emotion = self.get_emotion(emotion_id)
        if not emotion:
            raise BusinessException("情绪不存在")

        success = self.emotion_service.delete_emotion(emotion_id)
        if not success:
            raise BusinessException("删除失败")
        return success