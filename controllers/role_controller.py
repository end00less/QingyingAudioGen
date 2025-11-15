# app/controllers/role_controller.py
from typing import List, Optional

from app.controllers.base_controller import BaseController, BusinessException
from app.entity.role_entity import RoleEntity
from app.services.role_service import RoleService
from app.services.project_service import ProjectService
from app.services.line_service import LineService


class RoleController(BaseController):
    def __init__(self,
                 role_service: RoleService,
                 project_service: ProjectService,
                 line_service: LineService):
        self.role_service = role_service
        self.project_service = project_service
        self.line_service = line_service

    def create_role(self, project_id: int, name: str,
                    default_voice_id: int = None) -> RoleEntity:
        """创建角色"""
        project = self.project_service.get_project(project_id)
        if not project:
            raise BusinessException(f"项目 {project_id} 不存在")

        entity = RoleEntity(
            project_id=project_id,
            name=name,
            default_voice_id=default_voice_id
        )

        result = self.role_service.create_role(entity)
        if result is None:
            raise BusinessException(f"角色 '{name}' 已存在")
        return result

    def get_role(self, role_id: int) -> RoleEntity:
        """根据ID查询角色"""
        entity = self.role_service.get_role(role_id)
        if not entity:
            raise BusinessException(f"角色 {role_id} 不存在", 404)
        return entity

    def get_roles_by_project(self, project_id: int) -> List[RoleEntity]:
        """获取项目下所有角色"""
        project = self.project_service.get_project(project_id)
        if not project:
            raise BusinessException(f"项目 {project_id} 不存在")
        return self.role_service.get_all_roles(project_id)

    def update_role(self, role_id: int, **kwargs) -> bool:
        """更新角色"""
        role = self.get_role(role_id)
        if not role:
            raise BusinessException("角色不存在")

        success = self.role_service.update_role(role_id, kwargs)
        if not success:
            raise BusinessException("更新失败，角色名称可能已存在或项目ID被修改")
        return success

    def delete_role(self, role_id: int) -> bool:
        """删除角色"""
        role = self.get_role(role_id)
        if not role:
            raise BusinessException("角色不存在")

        # 清除该角色关联的台词
        self.line_service.clear_role_id(role_id)

        success = self.role_service.delete_role(role_id)
        if not success:
            raise BusinessException("删除失败")
        return success