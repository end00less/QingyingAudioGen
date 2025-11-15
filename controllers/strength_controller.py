# app/controllers/strength_controller.py
from typing import List, Optional

from app.controllers.base_controller import BaseController, BusinessException
from app.entity.strength_entity import StrengthEntity
from app.services.strength_service import StrengthService


class StrengthController(BaseController):
    def __init__(self, strength_service: StrengthService):
        self.strength_service = strength_service

    def create_strength(self, name: str, description: str = None) -> StrengthEntity:
        """创建情绪强度"""
        entity = StrengthEntity(name=name, description=description)

        result = self.strength_service.create_strength(entity)
        if result is None:
            raise BusinessException(f"情绪强度 '{name}' 已存在")
        return result

    def get_strength(self, strength_id: int) -> StrengthEntity:
        """根据ID查询情绪强度"""
        entity = self.strength_service.get_strength(strength_id)
        if not entity:
            raise BusinessException(f"情绪强度 {strength_id} 不存在", 404)
        return entity

    def get_strength_by_name(self, name: str) -> StrengthEntity:
        """根据名称查询情绪强度"""
        entity = self.strength_service.get_strength_by_name(name)
        if not entity:
            raise BusinessException(f"情绪强度 '{name}' 不存在", 404)
        return entity

    def get_all_strengths(self) -> List[StrengthEntity]:
        """获取所有情绪强度"""
        return self.strength_service.get_all_strengths()

    def update_strength(self, strength_id: int, **kwargs) -> bool:
        """更新情绪强度"""
        strength = self.get_strength(strength_id)
        if not strength:
            raise BusinessException("情绪强度不存在")

        success = self.strength_service.update_strength(strength_id, kwargs)
        if not success:
            raise BusinessException("更新失败，情绪强度名称可能已存在")
        return success

    def delete_strength(self, strength_id: int) -> bool:
        """删除情绪强度"""
        strength = self.get_strength(strength_id)
        if not strength:
            raise BusinessException("情绪强度不存在")

        success = self.strength_service.delete_strength(strength_id)
        if not success:
            raise BusinessException("删除失败")
        return success