from typing import Optional

from sqlalchemy import Sequence

from app.entity.strength_entity import StrengthEntity
from app.models.po import StrengthPO
from app.repositories.strength_repository import StrengthRepository


class StrengthService:

    def __init__(self, repository: StrengthRepository):
        """注入 repository"""
        self.repository = repository

    def create_strength(self, entity: StrengthEntity):
        """创建新情绪强弱枚举
        - 检查同名情绪强弱枚举是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """

        strength = self.repository.get_by_name(entity.name)
        if strength:
            return None
        # 手动将entity转化为po
        po = StrengthPO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = StrengthEntity(**data)

        # 将po转化为entity
        return entity

    # 在 app/services/strength_service.py 中添加
    def create_default_strengths(self):
        """创建默认强度数据"""
        default_strengths = [
            {"name": "微弱", "description": "几乎察觉不到的强度"},
            {"name": "稍弱", "description": "轻微的强度"},
            {"name": "中等", "description": "一般的强度"},
            {"name": "较强", "description": "明显的强度"},
            {"name": "强烈", "description": "非常强烈的强度"}
        ]

        created_count = 0
        for strength_data in default_strengths:
            # 检查是否已存在
            existing = self.repository.get_by_name(strength_data["name"])
            if not existing:
                # 创建强度
                strength_entity = StrengthEntity(
                    name=strength_data["name"],
                    description=strength_data["description"]
                )
                po = StrengthPO(**strength_entity.__dict__)
                self.repository.create(po)
                created_count += 1

        print(f"创建了 {created_count} 个默认强度")
        return created_count > 0

    def get_strength(self, strength_id: int) -> Optional[StrengthEntity]:
        """根据 ID 查询情绪强弱枚举"""
        po = self.repository.get_by_id(strength_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = StrengthEntity(**data)
        return res

    def get_all_strengths(self) -> Sequence[StrengthEntity]:
        """获取所有情绪强弱枚举列表"""
        pos = self.repository.get_all()
        # pos -> entities

        entities = [
            StrengthEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_strength(self, strength_id: int, data: dict) -> bool:
        """更新情绪强弱枚举
        - 可以只更新部分字段
        """

        name = data.get("name")
        if name and self.repository.get_by_name(name):
            return False
        self.repository.update(strength_id, data)
        return True

    def delete_strength(self, strength_id: int) -> bool:
        """删除情绪强弱枚举
        """
        res = self.repository.delete(strength_id)
        return res

    def get_strength_by_name(self, name: str) -> Optional[StrengthEntity]:
        """根据名称查询情绪强弱枚举"""
        po = self.repository.get_by_name(name)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = StrengthEntity(**data)
        return res
