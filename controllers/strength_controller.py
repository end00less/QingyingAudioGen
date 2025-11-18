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

    # 在 app/controllers/strength_controller.py 中添加
    def ensure_default_strengths(self) -> List[StrengthEntity]:
        """确保默认强度数据存在"""
        strengths = self.strength_service.get_all_strengths()

        if not strengths:
            print("强度数据为空，正在创建默认强度...")
            default_strengths = [
                {"name": "微弱", "description": "几乎察觉不到的强度"},
                {"name": "稍弱", "description": "轻微的强度"},
                {"name": "中等", "description": "一般的强度"},
                {"name": "较强", "description": "明显的强度"},
                {"name": "强烈", "description": "非常强烈的强度"}
            ]

            for strength_data in default_strengths:
                try:
                    self.create_strength(
                        name=strength_data["name"],
                        description=strength_data["description"]
                    )
                except BusinessException as e:
                    # 如果已经存在，忽略错误
                    if "已存在" not in str(e):
                        raise e

            # 重新获取强度列表
            strengths = self.strength_service.get_all_strengths()
            print(f"创建了 {len(strengths)} 个默认强度")

        return strengths

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