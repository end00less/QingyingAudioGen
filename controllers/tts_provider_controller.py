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

    def update_tts_provider(self, tts_provider_id: int, **kwargs) -> bool:
        """更新TTS服务商"""
        tts_provider = self.get_tts_provider(tts_provider_id)
        if not tts_provider:
            raise BusinessException("TTS服务商不存在")

        success = self.tts_provider_service.update_tts_provider(tts_provider_id, kwargs)
        if not success:
            raise BusinessException("更新失败，服务商名称可能已存在")
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