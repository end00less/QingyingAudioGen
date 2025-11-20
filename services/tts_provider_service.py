# app/services/tts_provider_service.py
from typing import Optional

import requests
from sqlalchemy import Sequence

from app.entity.tts_provider_entity import TTSProviderEntity
from app.models.po import TTSProviderPO
from app.repositories.tts_provider_repository import TTSProviderRepository


class TTSProviderService:

    def __init__(self, repository: TTSProviderRepository):
        """注入 repository"""
        self.repository = repository

    def get_all_tts_providers(self) -> list[TTSProviderEntity]:
        """查询所有tts供应商"""
        pos = self.repository.get_all()
        res = [TTSProviderEntity(**{k: v for k, v in po.__dict__.items() if not k.startswith("_")}) for po in pos]
        return res

    def get_tts_provider(self, tts_provider_id: int) -> Optional[TTSProviderEntity]:
        """根据 ID 查询tts供应商"""
        po = self.repository.get_by_id(tts_provider_id)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = TTSProviderEntity(**data)
        return res

    def get_tts_provider_by_name(self, name: str) -> Optional[TTSProviderEntity]:
        """根据名称查询tts供应商"""
        po = self.repository.get_by_name(name)
        if not po:
            return None
        data = {k: v for k, v in po.__dict__.items() if not k.startswith("_")}
        res = TTSProviderEntity(**data)
        return res

    def create_tts_provider(self, entity: TTSProviderEntity) -> TTSProviderEntity:
        """创建新的TTS服务商
        - 检查同名服务商是否存在
        - 如果存在，返回None
        - 调用 repository.create 插入数据库
        """
        # 检查同名服务商是否存在
        existing_provider = self.repository.get_by_name(entity.name)
        if existing_provider:
            return None

        # 手动将entity转化为po
        po = TTSProviderPO(
            name=entity.name,
            api_base_url=entity.api_base_url,
            api_key=entity.api_key,
            status=entity.status if entity.status is not None else 1
        )

        res = self.repository.create(po)

        # 将po转化为entity
        data = {k: v for k, v in res.__dict__.items() if not k.startswith("_")}
        entity = TTSProviderEntity(**data)
        return entity

    def update_tts_provider(self, tts_provider_id: int, data: dict) -> bool:
        """更新tts供应商
        - 可以只更新部分字段
        - 检查同名冲突
        """
        name = data.get("name")
        if name:
            # 检查同名冲突（排除自己）
            existing_provider = self.repository.get_by_name(name)
            if existing_provider and existing_provider.id != tts_provider_id:
                return False

        success = self.repository.update(tts_provider_id, data)
        return success

    def delete_tts_provider(self, tts_provider_id: int) -> bool:
        """删除tts供应商"""
        # 检查服务商是否存在
        provider = self.repository.get_by_id(tts_provider_id)
        if not provider:
            return False

        # 检查是否是默认服务商（index_tts），防止删除默认服务商
        if provider.name == "index_tts":
            return False

        res = self.repository.delete(tts_provider_id)
        return res

    def create_default_tts_provider(self):
        """创建默认的tts供应商"""
        if self.repository.get_by_name("index_tts"):
            return
        if self.repository.get_by_id(1):
            return
        po = TTSProviderPO(name="index_tts", id=1, status=1, api_base_url="", api_key="")
        self.repository.create(po)

    def test_tts_provider(self, entity: TTSProviderEntity) -> bool:
        """测试TTS服务商连接"""
        # 拿到url
        api_base_url = entity.api_base_url
        if not api_base_url:
            return False

        # ping api
        try:
            resp = requests.get(api_base_url, timeout=5)

            # 如果返回 200-399 都认为是通的（有些服务会 302 重定向）
            if 200 <= resp.status_code < 400:
                try:
                    data = resp.json()
                    if "endpoints" in data:
                        return True
                    else:
                        print("TTS provider test failed: 'endpoints' missing in response")
                        return False
                except ValueError:
                    print("TTS provider test failed: response is not valid JSON")
                    return False
            else:
                print(f"TTS provider test failed: status {resp.status_code}")
                return False

        except Exception as e:
            # 这里可以打印日志，方便排查
            print(f"TTS provider test failed: {e}")
            return False