import os
from typing import Optional

from sqlalchemy import Sequence

from app.entity.voice_entity import VoiceEntity
from app.models.po import VoicePO
from app.repositories.multi_emotion_voice_repository import MultiEmotionVoiceRepository
from app.repositories.voice_repository import VoiceRepository
from app.config.app_config import app_config  # 导入配置


class VoiceService:

    def __init__(self, repository: VoiceRepository,multi_emotion_voice_repository: MultiEmotionVoiceRepository):
        """注入 repository"""
        self.repository = repository
        self.multi_emotion_voice_repository = multi_emotion_voice_repository

    def create_voice(self,  entity: VoiceEntity):
        """创建新音色
        - 检查同名音色是否存在
        - 如果存在，抛出异常或返回错误
        - 调用 repository.create 插入数据库
        """

        voice = self.repository.get_by_name(entity.name, entity.tts_provider_id)
        if voice:
            return None
        # 手动将entity转化为po
        po = VoicePO(**entity.__dict__)
        res = self.repository.create(po)

        # res(po) --> entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = VoiceEntity(**data)

        # 将po转化为entity
        return entity


    def get_voice(self, voice_id: int) -> Optional[VoiceEntity]:
        """根据 ID 查询音色"""
        po = self.repository.get_by_id(voice_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = VoiceEntity(**data)
        return res

    def get_all_voices(self,tts_provider_id: int) -> Sequence[VoiceEntity]:
        """获取所有音色列表"""
        pos = self.repository.get_all(tts_provider_id)
        # pos -> entities

        entities = [
            VoiceEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")})
            for po in pos
        ]
        return entities

    def update_voice(self, voice_id: int, data:dict) -> bool:
        """更新音色
        - 可以只更新部分字段
        - 检查同名冲突
        - 检查project_id不能改变
        """
        name = data["name"]
        tts_provider_id = data["tts_provider_id"]
        if self.repository.get_by_name(name, tts_provider_id) and self.repository.get_by_name(name,tts_provider_id).id != voice_id:
            return False
        po = self.repository.get_by_id(voice_id)
        # 防止改变project_id
        if po.tts_provider_id != tts_provider_id:
            return False
        self.repository.update(voice_id, data)
        return True

    def delete_voice(self, voice_id: int) -> bool:
        """删除音色,需要保证事务
        """

        res = self.repository.delete(voice_id)
        self.multi_emotion_voice_repository.delete_multi_emotion_voice_by_voice_id(voice_id)
        return res

    def create_default_voices(self, tts_provider_id: int) -> list[VoiceEntity]:
        """创建默认音色库 - 使用绝对路径"""
        # 检查是否已有音色
        existing_voices = self.get_all_voices(tts_provider_id)
        if existing_voices:
            print(f"TTS服务商 {tts_provider_id} 下已有 {len(existing_voices)} 个音色，跳过创建默认音色")
            return []

        # 默认音色配置 - 使用绝对路径
        default_voice_configs = [
            {
                "name": "小行",
                "description": "温和的青年男声，适合旁白和主要男性角色",
                "reference_path": app_config.get_voice_sample_path("小行"),
                "is_multi_emotion": 0
            },
            {
                "name": "小晓",
                "description": "甜美的少女音，适合女主角和年轻女性角色",
                "reference_path": app_config.get_voice_sample_path("小晓"),
                "is_multi_emotion": 0
            },
            {
                "name": "小阳",
                "description": "沉稳的成年男声，适合长辈和权威角色",
                "reference_path": app_config.get_voice_sample_path("小阳"),
                "is_multi_emotion": 0
            },
            {
                "name": "小夏",
                "description": "活泼的女声，适合年轻女孩和活泼角色",
                "reference_path": app_config.get_voice_sample_path("小夏"),
                "is_multi_emotion": 0
            },
            {
                "name": "小东",
                "description": "磁性的男声，适合商业场景",
                "reference_path": app_config.get_voice_sample_path("小东"),
                "is_multi_emotion": 0
            },
            {
                "name": "小倩",
                "description": "温柔的女声，适合成熟女性角色",
                "reference_path": app_config.get_voice_sample_path("小倩"),
                "is_multi_emotion": 0
            },
            {
                "name": "小睿",
                "description": "睿智的解说音，适合知识类内容",
                "reference_path": app_config.get_voice_sample_path("小睿"),
                "is_multi_emotion": 0
            },
            {
                "name": "小悦",
                "description": "愉悦的播报音，适合新闻播报",
                "reference_path": app_config.get_voice_sample_path("小悦"),
                "is_multi_emotion": 0
            },
            {
                "name": "小龙",
                "description": "少年英雄音色，适合青少年角色",
                "reference_path": app_config.get_voice_sample_path("小龙"),
                "is_multi_emotion": 1
            },
            {
                "name": "小玉",
                "description": "仙女般音色，适合奇幻角色",
                "reference_path": app_config.get_voice_sample_path("小玉"),
                "is_multi_emotion": 1
            },
            {
                "name": "老陈",
                "description": "长者音色，适合老年角色",
                "reference_path": app_config.get_voice_sample_path("老陈"),
                "is_multi_emotion": 0
            },
            {
                "name": "小欢",
                "description": "欢快活泼音色，适合喜剧和欢乐场景",
                "reference_path": app_config.get_voice_sample_path("小欢"),
                "is_multi_emotion": 1
            },
            {
                "name": "小静",
                "description": "安静温柔音色，适合抒情场景",
                "reference_path": app_config.get_voice_sample_path("小静"),
                "is_multi_emotion": 1
            },
        ]

        created_voices = []
        missing_samples = []

        for config in default_voice_configs:
            try:
                # 检查样本文件是否存在
                if config["reference_path"] and not os.path.exists(config["reference_path"]):
                    missing_samples.append(config["name"])
                    print(f"⚠️  样本文件不存在: {config['reference_path']}")
                    # 使用空路径继续创建音色
                    config["reference_path"] = ""

                # 创建音色实体
                voice_entity = VoiceEntity(
                    tts_provider_id=tts_provider_id,
                    name=config["name"],
                    description=config["description"],
                    reference_path=config["reference_path"],
                    is_multi_emotion=config["is_multi_emotion"]
                )

                # 调用现有的create_voice方法
                voice = self.create_voice(voice_entity)
                if voice:
                    created_voices.append(voice)
                    print(f"✅ 创建默认音色: {config['name']}")
                else:
                    print(f"⚠️  音色已存在: {config['name']}")

            except Exception as e:
                print(f"❌ 创建音色失败 {config['name']}: {e}")

        if missing_samples:
            print(f"\n💡 提示: {len(missing_samples)} 个音色缺少样本文件")
            print("请将样本文件放入:", app_config.get_samples_dir())

        print(f"🎉 默认音色库创建完成! 共创建 {len(created_voices)} 个音色")
        return created_voices

    def initialize_default_voices(self, tts_provider_id: int) -> bool:
        """初始化默认音色库"""
        # 检查配置是否允许自动初始化
        if not app_config.should_auto_init_voices():
            print("配置禁止自动初始化默认音色")
            return False

        existing_voices = self.get_all_voices(tts_provider_id)
        if not existing_voices:
            created_voices = self.create_default_voices(tts_provider_id)
            return len(created_voices) > 0
        return False