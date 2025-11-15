# app/controllers/line_controller.py
import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor

from app.controllers.base_controller import BaseController, BusinessException
from app.dto.line_dto import LineCreateDTO, LineOrderDTO, LineAudioProcessDTO
from app.entity.line_entity import LineEntity
from app.services.line_service import LineService
from app.services.project_service import ProjectService
from app.services.chapter_service import ChapterService
from app.services.role_service import RoleService


class LineController(BaseController):
    def __init__(self,
                 line_service: LineService,
                 project_service: ProjectService,
                 chapter_service: ChapterService,
                 role_service: RoleService):
        self.line_service = line_service
        self.project_service = project_service
        self.chapter_service = chapter_service
        self.role_service = role_service
        self.tts_executor = ThreadPoolExecutor(max_workers=4)

    def create_line(self, chapter_id: int, text_content: str,
                    role_id: int = None, line_order: int = None,
                    emotion_id: int = None, strength_id: int = None) -> LineEntity:
        """创建台词"""
        chapter = self.chapter_service.get_chapter(chapter_id)
        if not chapter:
            raise BusinessException(f"章节 {chapter_id} 不存在")

        entity = LineEntity(
            chapter_id=chapter_id,
            text_content=text_content,
            role_id=role_id,
            line_order=line_order,
            emotion_id=emotion_id,
            strength_id=strength_id
        )

        result = self.line_service.create_line(entity)

        # 创建音频文件路径
        project = self.project_service.get_project(chapter.project_id)
        audio_path = f"{project.project_root_path}/{chapter.project_id}/{chapter_id}/audio"
        os.makedirs(audio_path, exist_ok=True)
        res_path = f"{audio_path}/id_{result.id}.wav"
        self.line_service.update_line(result.id, {"audio_path": res_path})

        return result

    def get_line(self, line_id: int) -> LineEntity:
        """根据ID查询台词"""
        entity = self.line_service.get_line(line_id)
        if not entity:
            raise BusinessException(f"台词 {line_id} 不存在", 404)
        return entity

    def get_lines_by_chapter(self, chapter_id: int) -> List[LineEntity]:
        """获取章节下所有台词"""
        chapter = self.chapter_service.get_chapter(chapter_id)
        if not chapter:
            raise BusinessException(f"章节 {chapter_id} 不存在")
        return self.line_service.get_all_lines(chapter_id)

    def update_line(self, line_id: int, **kwargs) -> bool:
        """更新台词"""
        line = self.get_line(line_id)
        if not line:
            raise BusinessException("台词不存在")

        success = self.line_service.update_line(line_id, kwargs)
        if not success:
            raise BusinessException("更新失败")
        return success

    def delete_line(self, line_id: int) -> bool:
        """删除台词"""
        line = self.get_line(line_id)
        if not line:
            raise BusinessException("台词不存在")

        success = self.line_service.delete_line(line_id)
        if not success:
            raise BusinessException("删除失败")
        return success

    def delete_all_lines(self, chapter_id: int) -> bool:
        """删除章节下所有台词"""
        chapter = self.chapter_service.get_chapter(chapter_id)
        if not chapter:
            raise BusinessException(f"章节 {chapter_id} 不存在")

        success = self.line_service.delete_all_lines(chapter_id)
        if not success:
            raise BusinessException("删除失败")
        return success

    def batch_update_line_order(self, line_orders: List[LineOrderDTO]) -> bool:
        """批量更新台词顺序"""
        if not line_orders:
            raise BusinessException("没有提供台词顺序数据")

        success = self.line_service.batch_update_line_order(line_orders)
        if not success:
            raise BusinessException("批量更新失败")
        return success

    def generate_audio(self, project_id: int, line_data: LineCreateDTO) -> bool:
        """生成音频（异步）"""
        # 这里可以集成到你的TTS队列系统
        # 当前先直接调用同步方法
        try:
            # 这里需要根据你的TTS系统实现具体的音频生成逻辑
            # 暂时返回成功
            self.line_service.update_line(line_data.id, {"status": "processing"})
            # 模拟音频生成完成
            self.line_service.update_line(line_data.id, {"status": "done"})
            return True
        except Exception as e:
            self.line_service.update_line(line_data.id, {"status": "failed"})
            raise BusinessException(f"音频生成失败: {str(e)}")

    def process_audio(self, line_id: int, process_dto: LineAudioProcessDTO) -> bool:
        """处理音频（变速、音量、裁剪等）"""
        line = self.get_line(line_id)
        if not line:
            raise BusinessException("台词不存在")

        success = self.line_service.process_audio(line_id, process_dto)
        if not success:
            raise BusinessException("音频处理失败")
        return success

    def export_audio_and_subtitle(self, chapter_id: int, single: bool = False) -> bool:
        """导出音频和字幕"""
        chapter = self.chapter_service.get_chapter(chapter_id)
        if not chapter:
            raise BusinessException(f"章节 {chapter_id} 不存在")

        success = self.line_service.export_audio(chapter_id, single)
        if not success:
            raise BusinessException("导出失败")
        return success

    def correct_subtitle(self, chapter_id: int) -> bool:
        """矫正字幕"""
        lines = self.get_lines_by_chapter(chapter_id)
        if not lines:
            raise BusinessException("无台词记录")

        paths = [line.audio_path for line in lines if line.audio_path]
        if not paths:
            raise BusinessException("未找到有效音频路径")

        # 读取所有台词文本
        text = "\n".join([line.text_content for line in lines if line.text_content])

        output_dir = os.path.join(os.path.dirname(paths[0]), "result")
        output_subtitle_path = os.path.join(output_dir, "result.srt")

        if not os.path.exists(output_subtitle_path):
            raise BusinessException("请先导出音频")

        # 整体字幕矫正
        self.line_service.correct_subtitle(text, output_subtitle_path)

        # 单条字幕矫正
        for line in lines:
            if line.subtitle_path and line.text_content and os.path.exists(line.subtitle_path):
                self.line_service.correct_subtitle(line.text_content, line.subtitle_path)

        return True