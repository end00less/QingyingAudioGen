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

    def parse_content_to_lines(self, project_id: int, chapter_id: int, progress_callback=None) -> List[LineInitDTO]:
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

        self.ensure_emotions_and_strengths()

        # 获取角色、情绪、强度信息
        roles = self.role_service.get_all_roles(project_id)
        role_names = set(role.name for role in roles)
        emotions = self.emotion_service.get_all_emotions()
        strengths = self.strength_service.get_all_strengths()

        # 详细的调试信息
        print(f"=== 调试信息 ===")
        print(f"情绪数量: {len(emotions)}")
        print(f"情绪列表: {[e.name for e in emotions]}")
        print(f"强度数量: {len(strengths)}")
        print(f"强度列表: {[s.name for s in strengths]}")
        print(f"=== 调试结束 ===")

        emotion_names = [emotion.name for emotion in emotions]
        strength_names = [strength.name for strength in strengths]
        emotions_dict = {emotion.name: emotion.id for emotion in emotions}
        strengths_dict = {strength.name: strength.id for strength in strengths}

        project = self.project_service.get_project(project_id)

        # 专门检查LLM配置
        if not project.llm_provider_id or not project.llm_model:
            raise BusinessException("项目未配置LLM服务，请先在项目设置中配置LLM服务商和模型")

        # 检查提示词配置，如果没有则使用默认提示词
        if not project.prompt_id:
            # 尝试获取默认提示词
            try:
                default_prompt = self.prompt_service.get_prompt_by_name("默认拆分台词提示词")
                if not default_prompt:
                    # 创建默认提示词
                    self.prompt_service.create_default_prompt()
                    default_prompt = self.prompt_service.get_prompt_by_name("默认拆分台词提示词")

                if default_prompt:
                    # 获取项目当前名称，构建完整的更新数据
                    current_project = self.project_service.get_project(project_id)
                    if current_project:
                        update_data = {
                            "name": current_project.name,  # 保持原有项目名称
                            "prompt_id": default_prompt.id  # 更新提示词ID
                        }
                        # 更新项目使用默认提示词
                        self.project_service.update_project(project_id, update_data)
                        project.prompt_id = default_prompt.id
                    else:
                        raise BusinessException("项目不存在")
                else:
                    raise BusinessException("无法获取默认提示词")
            except Exception as e:
                logging.error(f"设置默认提示词失败: {e}")
                raise BusinessException(f"提示词配置失败: {str(e)}")

        prompt = self.prompt_service.get_prompt(project.prompt_id)
        if not prompt:
            raise BusinessException("提示词不存在")

        total_segments = len(contents)

        # 通知进度：开始解析
        if progress_callback:
            progress_callback(0, total_segments, "开始解析章节内容...")

        for idx, content in enumerate(contents):
            try:
                # 更新进度
                if progress_callback:
                    progress_callback(idx + 1, total_segments, f"正在解析第 {idx + 1}/{total_segments} 段...")

                roles_list = list(role_names)

                # 添加调试信息
                logging.info(f"准备调用 LLM 解析第 {idx + 1} 段内容，长度: {len(content)} 字符")
                logging.info(f"可用角色: {roles_list}")
                logging.info(f"可用情绪: {emotion_names}")
                logging.info(f"可用强度: {strength_names}")

                result = self.chapter_service.para_content(
                    prompt.content, chapter_id, content,
                    roles_list, emotion_names, strength_names, project.is_precise_fill
                )

                # 调试：检查返回结果
                logging.info(f"LLM 返回结果: success={result.get('success')}, message={result.get('message')}")

                if not result["success"]:
                    raise BusinessException(result["message"])

                # 验证返回的数据格式
                lines_data = result["data"]
                if not isinstance(lines_data, list):
                    raise BusinessException(f"LLM返回数据格式错误，期望列表，得到 {type(lines_data)}")

                # 调试：检查数据条数和结构
                logging.info(f"LLM 返回数据条数: {len(lines_data)}")
                if lines_data and len(lines_data) > 0:
                    first_item = lines_data[0]
                    logging.info(f"第一条数据字段: {[attr for attr in dir(first_item) if not attr.startswith('_')]}")

                validated_lines = []
                for line_item in lines_data:
                    try:
                        # 如果 line_item 是字典而不是对象，转换为对象
                        if isinstance(line_item, dict):
                            from app.dto.line_dto import LineInitDTO
                            # 确保只传递必要的字段
                            line_data = LineInitDTO(
                                role_name=line_item.get('role_name', ''),
                                text_content=line_item.get('text_content', ''),
                                emotion_name=line_item.get('emotion_name'),
                                strength_name=line_item.get('strength_name')
                            )
                        else:
                            line_data = line_item

                        # 验证必要字段
                        if not hasattr(line_data, 'role_name') or not line_data.role_name:
                            logging.warning(f"跳过无效台词数据：缺少 role_name")
                            continue

                        if not hasattr(line_data, 'text_content') or not line_data.text_content:
                            logging.warning(f"跳过无效台词数据：缺少 text_content")
                            continue

                        # 确保没有意外的 title 字段
                        if hasattr(line_data, 'title'):
                            logging.warning(f"台词数据包含意外的 title 字段: {line_data.title}")
                            # 可以选择移除 title 字段或者忽略它

                        validated_lines.append(line_data)
                        role_names.add(line_data.role_name)

                    except Exception as e:
                        logging.error(f"处理台词数据失败: {e}")
                        continue

                all_line_data.extend(validated_lines)

                logging.info(f"第 {idx + 1} 段解析完成，获得 {len(validated_lines)} 条有效台词")

            except Exception as e:
                logging.error(f"解析第 {idx + 1} 段失败: {e}")
                logging.error(traceback.format_exc())
                if progress_callback:
                    progress_callback(idx + 1, total_segments, f"第 {idx + 1} 段解析失败: {str(e)}")
                raise BusinessException(f"解析失败：第 {idx + 1} 段处理出错: {str(e)}")

        # 保存到数据库
        try:
            # 更新进度：正在保存数据
            if progress_callback:
                progress_callback(total_segments, total_segments, f"正在保存 {len(all_line_data)} 条台词数据...")

            if not all_line_data:
                raise BusinessException("未解析出任何有效的台词数据")

            # 修复路径生成 - 使用 os.path.join 确保正确的路径分隔符
            import os
            audio_dir = os.path.normpath(os.path.join(
                project.project_root_path,
                str(project_id),
                str(chapter_id),
                "audio"
            ))
            os.makedirs(audio_dir, exist_ok=True)

            self.line_service.update_init_lines(
                all_line_data, project_id, chapter_id, emotions_dict, strengths_dict, audio_dir
            )

            # 更新进度：完成
            if progress_callback:
                progress_callback(total_segments, total_segments, "解析完成！")

            logging.info(f"章节 {chapter_id} 解析完成，共保存 {len(all_line_data)} 条台词")

        except Exception as e:
            logging.error(f"写入数据库失败: {e}")
            logging.error(traceback.format_exc())
            raise BusinessException(f"保存台词数据失败: {str(e)}")

        return all_line_data

    def ensure_emotions_and_strengths(self):
        """确保情绪和强度数据存在"""
        emotions = self.emotion_service.get_all_emotions()
        strengths = self.strength_service.get_all_strengths()

        if not emotions:
            print("情绪数据为空，正在创建默认情绪...")
            success = self.emotion_service.create_default_emotions()
            if not success:
                print("警告：创建默认情绪失败")

        if not strengths:
            print("强度数据为空，正在创建默认强度...")
            success = self.strength_service.create_default_strengths()
            if not success:
                print("警告：创建默认强度失败")

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

        # 修复这里的路径生成
        import os
        audio_dir = os.path.normpath(os.path.join(
            project.project_root_path,
            str(project_id),
            str(chapter_id),
            "audio"
        ))
        os.makedirs(audio_dir, exist_ok=True)

        self.line_service.update_init_lines(
            lines_data, project_id, chapter_id, emotions_dict, strengths_dict, audio_dir
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