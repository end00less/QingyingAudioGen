# app/controllers/llm_provider_controller.py
from typing import List, Optional

from app.controllers.base_controller import BaseController, BusinessException
from app.entity.llm_provider_entity import LLMProviderEntity
from app.services.llm_provider_service import LLMProviderService


class LLMProviderController(BaseController):
    def __init__(self, llm_provider_service: LLMProviderService):
        self.llm_provider_service = llm_provider_service

    def create_llm_provider(self, name: str, api_base_url: str,
                            api_key: str = None, model_list: dict = None,
                            custom_params: dict = None) -> LLMProviderEntity:
        """创建LLM服务商"""
        entity = LLMProviderEntity(
            name=name,
            api_base_url=api_base_url,
            api_key=api_key,
            model_list=model_list,
            custom_params=custom_params
        )

        result = self.llm_provider_service.create_llm_provider(entity)
        if result is None:
            raise BusinessException(f"LLM服务商 '{name}' 已存在")
        return result

    def get_llm_provider(self, llm_provider_id: int) -> LLMProviderEntity:
        """根据ID查询LLM服务商"""
        entity = self.llm_provider_service.get_llm_provider(llm_provider_id)
        if not entity:
            raise BusinessException(f"LLM服务商 {llm_provider_id} 不存在", 404)
        return entity

    def get_all_llm_providers(self) -> List[LLMProviderEntity]:
        """获取所有LLM服务商"""
        return self.llm_provider_service.get_all_llm_providers()

    def update_llm_provider(self, llm_provider_id: int, **kwargs) -> bool:
        """更新LLM服务商"""
        llm_provider = self.get_llm_provider(llm_provider_id)
        if not llm_provider:
            raise BusinessException("LLM服务商不存在")

        success = self.llm_provider_service.update_llm_provider(llm_provider_id, kwargs)
        if not success:
            raise BusinessException("更新失败，服务商名称可能已存在")
        return success

    def delete_llm_provider(self, llm_provider_id: int) -> bool:
        """删除LLM服务商"""
        llm_provider = self.get_llm_provider(llm_provider_id)
        if not llm_provider:
            raise BusinessException("LLM服务商不存在")

        success = self.llm_provider_service.delete_llm_provider(llm_provider_id)
        if not success:
            raise BusinessException("删除失败")
        return success

    def test_llm_provider(self, name: str, api_base_url: str,
                          api_key: str = None, model_list: dict = None,
                          custom_params: dict = None) -> bool:
        """测试LLM服务商"""
        entity = LLMProviderEntity(
            name=name,
            api_base_url=api_base_url,
            api_key=api_key,
            model_list=model_list,
            custom_params=custom_params
        )

        success, message = self.llm_provider_service.test_llm_provider(entity)
        if not success:
            raise BusinessException(f"测试失败: {message}")
        return True