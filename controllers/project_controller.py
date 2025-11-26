# app/controllers/project_controller.py
import os
import shutil
from typing import List, Optional

from app.controllers.base_controller import BaseController, BusinessException
from app.dto.project_dto import ProjectCreateDTO, ProjectResponseDTO
from app.entity.project_entity import ProjectEntity
from app.services.project_service import ProjectService
from app.services.chapter_service import ChapterService
from app.services.role_service import RoleService
from app.services.llm_provider_service import LLMProviderService
from app.services.tts_provider_service import TTSProviderService


class ProjectController(BaseController):
    def __init__(self,
                 project_service: ProjectService,
                 chapter_service: ChapterService,
                 role_service: RoleService,
                 llm_provider_service: LLMProviderService,
                 tts_provider_service: TTSProviderService):
        self.project_service = project_service
        self.chapter_service = chapter_service
        self.role_service = role_service
        self.llm_provider_service = llm_provider_service
        self.tts_provider_service = tts_provider_service

    def create_project(self, name: str, description: str = None,
                       project_root_path: str = None,
                       llm_provider_id: int = None,
                       llm_model: str = None,
                       tts_provider_id: int = None,
                       is_precise_fill: bool = False) -> ProjectEntity:
        """创建项目"""
        entity = ProjectEntity(
            name=name,
            description=description,
            project_root_path=project_root_path,
            llm_provider_id=llm_provider_id,
            llm_model=llm_model,
            tts_provider_id=tts_provider_id,
            is_precise_fill=is_precise_fill
        )

        result, message = self.project_service.create_project(entity)
        if result is None:
            raise BusinessException(message)
        return result

    def get_project(self, project_id: int) -> ProjectEntity:
        """根据ID查询项目"""
        entity = self.project_service.get_project(project_id)
        if not entity:
            raise BusinessException(f"项目 {project_id} 不存在", 404)
        return entity

    def get_all_projects(self) -> List[ProjectEntity]:
        """获取所有项目"""
        return self.project_service.get_all_projects()

    def update_project(self, project_id: int, **kwargs) -> bool:
        """更新项目"""
        project = self.get_project(project_id)
        if not project:
            raise BusinessException("项目不存在")

        success = self.project_service.update_project(project_id, kwargs)
        if not success:
            raise BusinessException("更新失败，项目名称可能已存在")
        return success

    def delete_project(self, project_id: int) -> bool:
        """删除项目（级联删除）"""
        project = self.get_project(project_id)
        if not project:
            raise BusinessException("项目不存在")

        # 级联删除项目所有相关内容
        chapters = self.chapter_service.get_all_chapters(project_id)
        for chapter in chapters:
            self.chapter_service.delete_chapter(chapter.id)

        # 删除项目目录
        project_path = os.path.join(project.project_root_path, str(project_id))
        if os.path.exists(project_path):
            shutil.rmtree(project_path)

        # 删除项目下所有角色
        roles = self.role_service.get_all_roles(project_id)
        for role in roles:
            self.role_service.delete_role(role.id)

        success = self.project_service.delete_project(project_id)
        if not success:
            raise BusinessException("删除失败")
        return success

    def import_novel_content(self, project_id: int, content: str) -> bool:
        """导入整本小说内容"""
        project = self.get_project(project_id)
        if not project:
            raise BusinessException("项目不存在")

        chapter_contents = self.project_service.parse_content(content)
        if not chapter_contents:
            raise BusinessException("导入失败，无法解析内容")

        # 批量创建章节
        for chapter_content in chapter_contents:
            name = chapter_content["chapter_name"]
            content_text = chapter_content["content"]
            self.chapter_service.create_chapter(
                ProjectEntity(project_id=project_id, title=name, text_content=content_text)
            )
        return True

    # 新增方法：获取LLM提供商列表
    def get_llm_providers(self):
        """获取所有LLM提供商"""
        return self.llm_provider_service.get_all_llm_providers()

    # 新增方法：获取TTS提供商列表
    def get_tts_providers(self):
        """获取所有TTS提供商"""
        return self.tts_provider_service.get_all_tts_providers()

    # 新增方法：根据提供商名称获取模型列表
    def get_llm_models_by_provider(self, provider_name):
        """根据提供商名称获取模型列表"""
        provider = self.llm_provider_service.get_llm_provider_by_name(provider_name)
        if provider and provider.model_list:
            # 将逗号分隔的字符串转换为列表
            model_names = [model.strip() for model in provider.model_list.split(',')]
            return model_names
        return []

    # 新增方法：根据名称获取LLM提供商ID
    def get_llm_provider_id_by_name(self, provider_name):
        """根据名称获取LLM提供商ID"""
        provider = self.llm_provider_service.get_llm_provider_by_name(provider_name)
        return provider.id if provider else None

    # 新增方法：根据名称获取TTS提供商ID
    def get_tts_provider_id_by_name(self, provider_name):
        """根据名称获取TTS提供商ID"""
        provider = self.tts_provider_service.get_tts_provider_by_name(provider_name)
        return provider.id if provider else None