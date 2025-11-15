# ui/export_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import json
import threading
from app.core.app_context import AppContext
from app.controllers.base_controller import BusinessException

class ExportDialog:
    def __init__(self, parent, chapter_id, project, app_controller):
        self.parent = parent
        self.chapter_id = chapter_id
        self.project = project
        self.app_controller = app_controller
        self.line_controller = app_controller.line_controller
        self.chapter_controller = app_controller.chapter_controller

        self.setup_dialog()

    def setup_dialog(self):
        """设置导出对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("项目导出")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)

        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 导出选项框架
        options_frame = ttk.LabelFrame(main_frame, text="导出选项", padding="10")
        options_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 导出路径
        ttk.Label(options_frame, text="导出路径:").pack(anchor=tk.W, pady=(0, 5))
        path_frame = ttk.Frame(options_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))

        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(path_frame, text="浏览", command=self.browse_path).pack(side=tk.RIGHT)

        # 导出格式
        ttk.Label(options_frame, text="导出格式:").pack(anchor=tk.W, pady=(0, 5))

        self.export_audio_var = tk.BooleanVar(value=True)
        self.export_subtitle_var = tk.BooleanVar(value=True)
        self.export_data_var = tk.BooleanVar(value=True)
        self.export_single_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(options_frame, text="导出合并音频", variable=self.export_audio_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="导出字幕文件", variable=self.export_subtitle_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="导出台词数据", variable=self.export_data_var).pack(anchor=tk.W, pady=2)
        ttk.Checkbutton(options_frame, text="导出单个音频文件", variable=self.export_single_var).pack(anchor=tk.W, pady=2)

        # 音频格式
        ttk.Label(options_frame, text="音频格式:").pack(anchor=tk.W, pady=(10, 5))
        self.audio_format_var = tk.StringVar(value="wav")
        format_frame = ttk.Frame(options_frame)
        format_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Radiobutton(format_frame, text="WAV", variable=self.audio_format_var, value="wav").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(format_frame, text="MP3", variable=self.audio_format_var, value="mp3").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(format_frame, text="FLAC", variable=self.audio_format_var, value="flac").pack(side=tk.LEFT)

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="开始导出", command=self.start_export).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy).pack(side=tk.LEFT)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, pady=(5, 0))

        # 设置默认导出路径
        default_path = os.path.join(self.project.project_root_path, "exports")
        self.path_var.set(default_path)

    def browse_path(self):
        """选择导出路径"""
        path = filedialog.askdirectory(title="选择导出路径")
        if path:
            self.path_var.set(path)

    def start_export(self):
        """开始导出"""
        export_path = self.path_var.get().strip()
        if not export_path:
            messagebox.showwarning("警告", "请选择导出路径")
            return

        if not any([self.export_audio_var.get(), self.export_subtitle_var.get(), self.export_data_var.get()]):
            messagebox.showwarning("警告", "请至少选择一种导出格式")
            return

        # 创建导出目录
        try:
            os.makedirs(export_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("错误", f"创建导出目录失败: {str(e)}")
            return

        # 在新线程中执行导出
        thread = threading.Thread(target=self._run_export, args=(export_path,))
        thread.daemon = True
        thread.start()

    def _run_export(self, export_path: str):
        """执行导出"""
        try:
            self.status_var.set("准备导出数据...")

            # 获取章节和台词数据
            chapter = self.chapter_controller.get_chapter(self.chapter_id)
            lines = self.line_controller.get_lines_by_chapter(self.chapter_id)

            if not lines:
                self.dialog.after(0, lambda: messagebox.showwarning("警告", "没有可导出的台词数据"))
                return

            # 导出台词数据
            if self.export_data_var.get():
                self.status_var.set("导出台词数据...")
                self._export_data(export_path, chapter, lines)

            # 导出音频文件
            if self.export_audio_var.get():
                self.status_var.set("处理音频文件...")
                self._export_audio(export_path, chapter, lines)

            # 导出字幕文件
            if self.export_subtitle_var.get():
                self.status_var.set("生成字幕文件...")
                self._export_subtitles(export_path, chapter, lines)

            self.status_var.set("导出完成！")
            self.dialog.after(0, lambda: messagebox.showinfo("成功", f"项目导出完成！\n导出路径: {export_path}"))

        except BusinessException as e:
            self.status_var.set(f"导出失败: {e.message}")
            self.dialog.after(0, lambda: messagebox.showerror("错误", e.message))
        except Exception as e:
            self.status_var.set(f"导出失败: {str(e)}")
            self.dialog.after(0, lambda: messagebox.showerror("错误", f"导出失败: {str(e)}"))

    def _export_data(self, export_path: str, chapter, lines):
        """导出台词数据"""
        # 导出为JSON
        json_data = {
            'project': {
                'id': self.project.id,
                'name': self.project.name,
                'description': self.project.description
            },
            'chapter': {
                'id': chapter.id,
                'title': chapter.title,
                'order_index': chapter.order_index
            },
            'lines': [
                {
                    'id': line.id,
                    'line_order': line.line_order,
                    'role_id': line.role_id,
                    'text_content': line.text_content,
                    'emotion_id': line.emotion_id,
                    'strength_id': line.strength_id,
                    'audio_path': line.audio_path,
                    'status': line.status
                }
                for line in lines
            ]
        }

        json_path = os.path.join(export_path, f"{chapter.title}_data.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

    def _export_audio(self, export_path: str, chapter, lines):
        """导出音频文件"""
        # 收集所有音频文件路径
        audio_paths = []
        for line in lines:
            if line.audio_path and os.path.exists(line.audio_path):
                audio_paths.append(line.audio_path)

        if audio_paths:
            # 导出合并音频
            if len(audio_paths) > 1:
                merged_audio_path = os.path.join(export_path, f"{chapter.title}_merged.{self.audio_format_var.get()}")
                # 这里调用音频合并逻辑
                # audio_processor.merge_audios(audio_paths, merged_audio_path)

            # 导出单个音频文件
            if self.export_single_var.get():
                single_audio_dir = os.path.join(export_path, "single_audio")
                os.makedirs(single_audio_dir, exist_ok=True)

                for i, audio_path in enumerate(audio_paths):
                    if i < len(lines):
                        line = lines[i]
                        role_name = self._get_role_name(line.role_id)
                        new_filename = f"{i + 1:03d}_{role_name}.{self.audio_format_var.get()}"
                        new_path = os.path.join(single_audio_dir, new_filename)
                        shutil.copy2(audio_path, new_path)

    def _export_subtitles(self, export_path: str, chapter, lines):
        """导出字幕文件"""
        # 生成合并音频的字幕
        if self.export_audio_var.get():
            merged_audio_path = os.path.join(export_path, f"{chapter.title}_merged.wav")
            if os.path.exists(merged_audio_path):
                subtitle_path = os.path.join(export_path, f"{chapter.title}_merged.srt")
                # 这里调用字幕生成逻辑
                # generate_subtitle(merged_audio_path, subtitle_path)

        # 生成单个音频的字幕
        if self.export_single_var.get():
            single_subtitle_dir = os.path.join(export_path, "single_subtitles")
            os.makedirs(single_subtitle_dir, exist_ok=True)

            for i, line in enumerate(lines):
                if line.audio_path and os.path.exists(line.audio_path):
                    subtitle_path = os.path.join(single_subtitle_dir, f"{i + 1:03d}.srt")
                    # 这里调用字幕生成逻辑
                    # generate_subtitle(line.audio_path, subtitle_path)

    def _get_role_name(self, role_id: int) -> str:
        """获取角色名称"""
        if not role_id:
            return "旁白"
        try:
            role = self.app_controller.role_controller.get_role(role_id)
            return role.name if role else "未知"
        except BusinessException:
            return "未知"