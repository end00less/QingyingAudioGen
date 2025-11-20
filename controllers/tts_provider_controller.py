# app/controllers/tts_provider_controller.py
from typing import List, Optional

from app.controllers.base_controller import BaseController, BusinessException
from app.entity.tts_provider_entity import TTSProviderEntity
from app.services.tts_provider_service import TTSProviderService


class TTSProviderController(BaseController):
    def __init__(self, tts_provider_service: TTSProviderService):
        self.tts_provider_service = tts_provider_service

    def get_tts_provider(self, tts_provider_id: int) -> TTSProviderEntity:
        """根据ID查询TTS服务商"""
        entity = self.tts_provider_service.get_tts_provider(tts_provider_id)
        if not entity:
            raise BusinessException(f"TTS服务商 {tts_provider_id} 不存在", 404)
        return entity

    def get_all_tts_providers(self) -> List[TTSProviderEntity]:
        """获取所有TTS服务商"""
        return self.tts_provider_service.get_all_tts_providers()

    def create_tts_provider(self, name: str, api_base_url: str,
                            api_key: str = None, status: int = 1) -> TTSProviderEntity:
        """创建TTS服务商"""
        # 检查参数
        if not name or not name.strip():
            raise BusinessException("服务商名称不能为空")
        if not api_base_url or not api_base_url.strip():
            raise BusinessException("API Base URL不能为空")

        # 创建实体
        entity = TTSProviderEntity(
            name=name.strip(),
            api_base_url=api_base_url.strip(),
            api_key=api_key.strip() if api_key else None,
            status=status
        )

        # 调用服务层创建
        result = self.tts_provider_service.create_tts_provider(entity)
        if result is None:
            raise BusinessException(f"TTS服务商 '{name}' 已存在")
        return result

    def update_tts_provider(self, tts_provider_id: int, **kwargs) -> bool:
        """更新TTS服务商"""
        tts_provider = self.get_tts_provider(tts_provider_id)
        if not tts_provider:
            raise BusinessException("TTS服务商不存在")

        # 过滤掉None值
        update_data = {k: v for k, v in kwargs.items() if v is not None}

        success = self.tts_provider_service.update_tts_provider(tts_provider_id, update_data)
        if not success:
            raise BusinessException("更新失败，服务商名称可能已存在")
        return success

    def delete_tts_provider(self, tts_provider_id: int) -> bool:
        """删除TTS服务商"""
        tts_provider = self.get_tts_provider(tts_provider_id)
        if not tts_provider:
            raise BusinessException("TTS服务商不存在")

        # 防止删除默认服务商
        if tts_provider.name == "index_tts":
            raise BusinessException("不能删除默认的TTS服务商")

        success = self.tts_provider_service.delete_tts_provider(tts_provider_id)
        if not success:
            raise BusinessException("删除失败")
        return success

    def test_tts_provider(self, name: str, api_base_url: str,
                          api_key: str = None) -> bool:
        """测试TTS服务商"""
        entity = TTSProviderEntity(
            name=name,
            api_base_url=api_base_url,
            api_key=api_key
        )

        success = self.tts_provider_service.test_tts_provider(entity)
        if not success:
            raise BusinessException("TTS服务商测试失败")
        return True