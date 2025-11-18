from typing import Optional

from sqlalchemy import Sequence

from app.entity.emotion_entity import EmotionEntity
from app.models.po import EmotionPO
from app.repositories.emotion_repository import EmotionRepository


class EmotionService:

    def __init__(self, repository: EmotionRepository):
        """注入 repository"""
        self.repository = repository

    def create_emotion(self,  entity: EmotionEntity):
        """创建新情绪枚举
        - 检查同名情绪枚举是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """

        emotion = self.repository.get_by_name(entity.name)
        if emotion:
            return None
        # 手动将entity转化为po
        po = EmotionPO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = EmotionEntity(**data)

        # 将po转化为entity
        return entity

    # 在 app/services/emotion_service.py 中添加
    def create_default_emotions(self):
        """创建默认情绪数据"""
        default_emotions = [
            {"name": "高兴", "description": "开心、愉悦的情绪"},
            {"name": "生气", "description": "愤怒、不满的情绪"},
            {"name": "伤心", "description": "悲伤、难过的情绪"},
            {"name": "害怕", "description": "恐惧、担忧的情绪"},
            {"name": "厌恶", "description": "讨厌、反感的情绪"},
            {"name": "低落", "description": "沮丧、失落的情绪"},
            {"name": "惊喜", "description": "惊讶、意外的情绪"},
            {"name": "平静", "description": "中性、平稳的情绪"}
        ]

        created_count = 0
        for emotion_data in default_emotions:
            # 检查是否已存在
            existing = self.repository.get_by_name(emotion_data["name"])
            if not existing:
                # 创建情绪
                emotion_entity = EmotionEntity(
                    name=emotion_data["name"],
                    description=emotion_data["description"]
                )
                po = EmotionPO(**emotion_entity.__dict__)
                self.repository.create(po)
                created_count += 1

        print(f"创建了 {created_count} 个默认情绪")
        return created_count > 0


    def get_emotion(self, emotion_id: int) -> Optional[EmotionEntity]:
        """根据 ID 查询情绪枚举"""
        po = self.repository.get_by_id(emotion_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = EmotionEntity(**data)
        return res

    def get_all_emotions(self) -> Sequence[EmotionEntity]:
        """获取所有情绪枚举列表"""
        pos = self.repository.get_all()
        # pos -> entities

        entities = [
            EmotionEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_emotion(self, emotion_id: int, data:dict) -> bool:
        """更新情绪枚举
        - 可以只更新部分字段
        """
        name = data.get("name")
        if self.repository.get_by_name(name):
            return False
        self.repository.update(emotion_id, data)
        return True

    def delete_emotion(self, emotion_id: int) -> bool:
        """删除情绪枚举
        """
        res = self.repository.delete(emotion_id)
        return res

    def get_emotion_by_name(self, name: str) -> Optional[EmotionEntity]:
        """根据名称查询情绪枚举"""
        po = self.repository.get_by_name(name)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = EmotionEntity(**data)
        return res
