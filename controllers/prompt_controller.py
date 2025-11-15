# app/controllers/prompt_controller.py
from typing import List, Optional

from app.controllers.base_controller import BaseController, BusinessException
from app.core.enums import TaskEnum
from app.entity.prompt_entity import PromptEntity
from app.services.prompt_service import PromptService


class PromptController(BaseController):
    def __init__(self, prompt_service: PromptService):
        self.prompt_service = prompt_service

    def create_prompt(self, name: str, task: str, content: str,
                      description: str = None) -> PromptEntity:
        """创建提示词"""
        # 验证任务类型
        if task not in [t.value for t in TaskEnum]:
            raise BusinessException(f"任务类型 '{task}' 不存在")

        entity = PromptEntity(
            name=name,
            task=task,
            content=content,
            description=description
        )

        result = self.prompt_service.create_prompt(entity)
        if result is None:
            raise BusinessException("创建失败，提示词名称可能已存在或数据不完整")
        return result

    def get_prompt(self, prompt_id: int) -> PromptEntity:
        """根据ID查询提示词"""
        entity = self.prompt_service.get_prompt(prompt_id)
        if not entity:
            raise BusinessException(f"提示词 {prompt_id} 不存在", 404)
        return entity

    def get_prompt_by_name(self, name: str) -> PromptEntity:
        """根据名称查询提示词"""
        entity = self.prompt_service.get_prompt_by_name(name)
        if not entity:
            raise BusinessException(f"提示词 '{name}' 不存在", 404)
        return entity

    def get_all_prompts(self) -> List[PromptEntity]:
        """获取所有提示词"""
        return self.prompt_service.get_all_prompts()

    def update_prompt(self, prompt_id: int, **kwargs) -> bool:
        """更新提示词"""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            raise BusinessException("提示词不存在")

        success = self.prompt_service.update_prompt(prompt_id, kwargs)
        if not success:
            raise BusinessException("更新失败，提示词名称可能已存在或数据不完整")
        return success

    def delete_prompt(self, prompt_id: int) -> bool:
        """删除提示词"""
        prompt = self.get_prompt(prompt_id)
        if not prompt:
            raise BusinessException("提示词不存在")

        success = self.prompt_service.delete_prompt(prompt_id)
        if not success:
            raise BusinessException("删除失败")
        return success

    def get_prompts_by_task(self, task: str) -> List[PromptEntity]:
        """根据任务类型获取提示词"""
        if task not in [t.value for t in TaskEnum]:
            raise BusinessException(f"任务类型 '{task}' 不存在")
        return self.prompt_service.get_prompt_by_task(task)

    def get_all_tasks(self) -> List[str]:
        """获取所有任务类型"""
        return self.prompt_service.get_all_tasks()

    def create_default_prompt(self) -> bool:
        """创建默认提示词"""
        success = self.prompt_service.create_default_prompt()
        if not success:
            raise BusinessException("创建默认提示词失败")
        return success