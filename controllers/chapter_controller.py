# app/controllers/chapter_controller.py
import json
import logging
import traceback
from typing import List, Optional, Dict, Any

from app.controllers.base_controller import BaseController, BusinessException
from app.dto.chapter_dto import ChapterCreateDTO
from app.dto.line_dto import LineInitDTO
from app.entity.chapter_entity import ChapterEntity
from app.services.chapter_service import ChapterService
from app.services.project_service import ProjectService
from app.services.line_service import LineService
from app.services.role_service import RoleService
from app.services.emotion_service import EmotionService
from app.services.strength_service import StrengthService
from app.services.prompt_service import PromptService
from app.services.voice_service import VoiceService


class ChapterController(BaseController):
    def __init__(self,
                 chapter_service: ChapterService,
                 project_service: ProjectService,
                 line_service: LineService,
                 role_service: RoleService,
                 emotion_service: EmotionService,
                 strength_service: StrengthService,
                 prompt_service: PromptService,
                 voice_service: VoiceService):
        self.chapter_service = chapter_service
        self.project_service = project_service
        self.line_service = line_service
        self.role_service = role_service
        self.emotion_service = emotion_service
        self.strength_service = strength_service
        self.prompt_service = prompt_service
        self.voice_service = voice_service

    def create_chapter(self, project_id: int, title: str,
                       text_content: str = None, order_index: int = None) -> ChapterEntity:
        """创建章节"""
        # 验证项目存在
        project = self.project_service.get_project(project_id)
        if not project:
            raise BusinessException(f"项目 {project_id} 不存在")

        entity = ChapterEntity(
            project_id=project_id,
            title=title,
            text_content=text_content,
            order_index=order_index
        )

        result = self.chapter_service.create_chapter(entity)
        if result is None:
            raise BusinessException(f"章节 '{title}' 已存在")
        return result

    def get_chapter(self, chapter_id: int) -> ChapterEntity:
        """根据ID查询章节"""
        entity = self.chapter_service.get_chapter(chapter_id)
        if not entity:
            raise BusinessException(f"章节 {chapter_id} 不存在", 404)
        return entity

    def get_chapters_by_project(self, project_id: int) -> List[ChapterEntity]:
        """获取项目下所有章节"""
        project = self.project_service.get_project(project_id)
        if not project:
            raise BusinessException(f"项目 {project_id} 不存在")
        return self.chapter_service.get_all_chapters(project_id)

    def update_chapter(self, chapter_id: int, **kwargs) -> bool:
        """更新章节"""
        chapter = self.get_chapter(chapter_id)
        if not chapter:
            raise BusinessException("章节不存在")

        success = self.chapter_service.update_chapter(chapter_id, kwargs)
        if not success:
            raise BusinessException("更新失败，章节名称可能已存在")
        return success

    def delete_chapter(self, chapter_id: int) -> bool:
        """删除章节"""
        chapter = self.get_chapter(chapter_id)
        if not chapter:
            raise BusinessException("章节不存在")

        success = self.chapter_service.delete_chapter(chapter_id)
        if not success:
            raise BusinessException("删除失败")
        return success

    def parse_content_to_lines(self, project_id: int, chapter_id: int) -> List[LineInitDTO]:
        """解析章节内容为台词"""
        chapter = self.get_chapter(chapter_id)
        if not chapter.text_content:
            raise BusinessException("章节内容不存在")

        try:
            contents = self.chapter_service.split_text(chapter_id, 1500)
        except Exception as e:
            logging.error(f"章节拆分失败: {e}")
            raise BusinessException("章节拆分失败")

        all_line_data = []

        # 获取角色、情绪、强度信息
        roles = self.role_service.get_all_roles(project_id)
        role_names = set(role.name for role in roles)
        emotions = self.emotion_service.get_all_emotions()
        strengths = self.strength_service.get_all_strengths()

        emotion_names = [emotion.name for emotion in emotions]
        strength_names = [strength.name for strength in strengths]
        emotions_dict = {emotion.name: emotion.id for emotion in emotions}
        strengths_dict = {strength.name: strength.id for strength in strengths}

        project = self.project_service.get_project(project_id)
        if not project.tts_provider_id or not project.llm_provider_id or not project.llm_model:
            raise BusinessException("项目未配置TTS/LLM服务")

        prompt = self.prompt_service.get_prompt(project.prompt_id) if project.prompt_id else None
        if not prompt:
            raise BusinessException("提示词不存在")

        for idx, content in enumerate(contents):
            try:
                roles_list = list(role_names)
                result = self.chapter_service.para_content(
                    prompt.content, chapter_id, content,
                    roles_list, emotion_names, strength_names, project.is_precise_fill
                )

                if not result["success"]:
                    raise BusinessException(result["message"])

                # 提取新角色
                lines_data = result["data"]
                for line_data in lines_data:
                    role_names.add(line_data.role_name)

                all_line_data.extend(lines_data)

            except Exception as e:
                logging.error(f"解析第 {idx + 1} 段失败: {e}")
                raise BusinessException(f"解析失败：第 {idx + 1} 段处理出错")

        # 保存到数据库
        try:
            audio_path = f"{project.project_root_path}/{project_id}/{chapter_id}/audio"
            import os
            os.makedirs(audio_path, exist_ok=True)
            self.line_service.update_init_lines(
                all_line_data, project_id, chapter_id, emotions_dict, strengths_dict, audio_path
            )
        except Exception as e:
            logging.error(f"写入数据库失败: {e}")
            raise BusinessException("写入数据库失败")

        return all_line_data

    def export_llm_prompt(self, project_id: int, chapter_id: int) -> str:
        """导出LLM提示词"""
        roles = self.role_service.get_all_roles(project_id)
        role_names = [role.name for role in roles]
        emotions = self.emotion_service.get_all_emotions()
        strengths = self.strength_service.get_all_strengths()

        emotion_names = [emotion.name for emotion in emotions]
        strength_names = [strength.name for strength in strengths]

        project = self.project_service.get_project(project_id)
        prompt = self.prompt_service.get_prompt(project.prompt_id) if project.prompt_id else None
        chapter = self.chapter_service.get_chapter(chapter_id)
        content = chapter.text_content

        if not prompt:
            raise BusinessException("提示词不存在")

        return self.chapter_service.fill_prompt(
            prompt.content, role_names, emotion_names, strength_names, content
        )

    def import_external_lines(self, project_id: int, chapter_id: int,
                              json_data: str) -> bool:
        """导入第三方JSON台词数据"""
        try:
            lines_data = json.loads(json_data)
        except json.JSONDecodeError:
            raise BusinessException("JSON格式错误")

        emotions = self.emotion_service.get_all_emotions()
        strengths = self.strength_service.get_all_strengths()

        emotions_dict = {emotion.name: emotion.id for emotion in emotions}
        strengths_dict = {strength.name: strength.id for strength in strengths}

        project = self.project_service.get_project(project_id)

        # 精准填充处理
        if project.is_precise_fill == 1:
            from app.core.text_correct_engine import TextCorrectorFinal
            corrector = TextCorrectorFinal()
            content = self.chapter_service.get_chapter(chapter_id).text_content
            if content:
                lines_data = corrector.correct_ai_text(content, lines_data)

        lines_data = [LineInitDTO(**line) for line in lines_data]

        audio_path = f"{project.project_root_path}/{project_id}/{chapter_id}/audio"
        import os
        os.makedirs(audio_path, exist_ok=True)

        self.line_service.update_init_lines(
            lines_data, project_id, chapter_id, emotions_dict, strengths_dict, audio_path
        )
        return True

    def smart_match_voice(self, project_id: int, chapter_id: int) -> List[Dict]:
        """智能匹配角色和音色"""
        project = self.project_service.get_project(project_id)
        if not project:
            raise BusinessException("项目不存在")

        # 获取未绑定音色的角色
        roles = self.role_service.get_all_roles(project_id)
        roles_no_voice = [role for role in roles if role.default_voice_id is None]
        role_names = [role.name for role in roles_no_voice]

        # 获取所有音色
        voices = self.voice_service.get_all_voices(project.tts_provider_id)
        voice_names = [
            {"name": voice.name, "description": voice.description}
            for voice in voices
        ]

        # 获取章节内容
        content = self.chapter_service.get_chapter(chapter_id).text_content

        success, matched_data = self.chapter_service.add_smart_role_and_voice(
            project, content, role_names, voice_names
        )

        if not success:
            raise BusinessException("智能匹配失败")
        return matched_data