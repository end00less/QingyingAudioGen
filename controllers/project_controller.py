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


class ProjectController(BaseController):
    def __init__(self,
                 project_service: ProjectService,
                 chapter_service: ChapterService,
                 role_service: RoleService):
        self.project_service = project_service
        self.chapter_service = chapter_service
        self.role_service = role_service

    # 在 ProjectController 中修改
    def create_project(self, name: str, description: str = None,
                       project_root_path: str = None,
                       llm_model: str = None,
                       is_precise_fill: bool = False) -> ProjectEntity:
        """创建项目"""
        entity = ProjectEntity(
            name=name,
            description=description,
            project_root_path=project_root_path,
            llm_model=llm_model,
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