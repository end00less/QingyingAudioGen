# app/ui/voice_dialog.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
import os
import threading
import time

from app.entity.voice_entity import VoiceEntity
from app.services.audio_player_service import audio_player


class VoiceDialog:
    def __init__(self, parent, tts_provider_id: int, app_controller, voice: Optional[VoiceEntity] = None):
        self.parent = parent
        self.tts_provider_id = tts_provider_id
        self.app_controller = app_controller
        self.voice = voice
        self.result = None

        # 播放状态
        self.is_playing = False
        self.current_playing_path = None
        self.play_thread = None

        self.setup_dialog()

    def setup_dialog(self):
        """设置对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑音色" if self.voice else "新建音色")
        self.dialog.geometry("500x450")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.create_widgets()

    def create_widgets(self):
        """创建控件"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 音色名称
        ttk.Label(main_frame, text="音色名称:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.name_var = tk.StringVar()
        if self.voice:
            self.name_var.set(self.voice.name)
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        # 音色描述
        ttk.Label(main_frame, text="音色描述:").grid(row=1, column=0, sticky=tk.NW, pady=10)
        self.desc_text = tk.Text(main_frame, width=30, height=4)
        self.desc_text.grid(row=1, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        if self.voice and self.voice.description:
            self.desc_text.insert('1.0', self.voice.description)

        # 参考音频路径
        ttk.Label(main_frame, text="参考音频路径:").grid(row=2, column=0, sticky=tk.W, pady=10)
        self.ref_path_var = tk.StringVar()
        if self.voice:
            self.ref_path_var.set(self.voice.reference_path or "")

        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=2, column=1, sticky=tk.W + tk.E, pady=10, padx=(10, 0))

        self.ref_path_entry = ttk.Entry(path_frame, textvariable=self.ref_path_var, width=25)
        self.ref_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            path_frame,
            text="浏览",
            command=self.browse_audio_file,
            width=8
        ).pack(side=tk.RIGHT, padx=(5, 0))

        # 音频预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="音频预览", padding="10")
        preview_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W + tk.E, pady=10, padx=(0, 10))

        # 预览按钮和状态
        preview_btn_frame = ttk.Frame(preview_frame)
        preview_btn_frame.pack(fill=tk.X)

        self.preview_btn = ttk.Button(
            preview_btn_frame,
            text="▶ 预览播放",
            command=self.toggle_preview_audio,
            width=12
        )
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.preview_status_var = tk.StringVar(value="请选择音频文件")
        preview_status_label = ttk.Label(
            preview_btn_frame,
            textvariable=self.preview_status_var,
            foreground="gray"
        )
        preview_status_label.pack(side=tk.LEFT)

        # 文件信息
        file_info_frame = ttk.Frame(preview_frame)
        file_info_frame.pack(fill=tk.X, pady=(5, 0))

        self.file_info_var = tk.StringVar()
        file_info_label = ttk.Label(
            file_info_frame,
            textvariable=self.file_info_var,
            font=("Arial", 9),
            foreground="blue"
        )
        file_info_label.pack(anchor=tk.W)

        # 绑定路径变化事件
        self.ref_path_var.trace('w', self.on_path_changed)
        # 初始更新一次状态
        self.on_path_changed()

        # 多情绪音色
        self.multi_emotion_var = tk.BooleanVar()
        if self.voice:
            self.multi_emotion_var.set(self.voice.is_multi_emotion == 1)

        emotion_frame = ttk.Frame(main_frame)
        emotion_frame.grid(row=4, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        ttk.Checkbutton(
            emotion_frame,
            text="多情绪音色",
            variable=self.multi_emotion_var,
            command=self.on_multi_emotion_changed
        ).pack(side=tk.LEFT)

        # 多情绪音色提示
        self.emotion_tip_var = tk.StringVar(value="启用后可为不同情绪配置不同音频")
        emotion_tip_label = ttk.Label(
            emotion_frame,
            textvariable=self.emotion_tip_var,
            font=("Arial", 9),
            foreground="green"
        )
        emotion_tip_label.pack(side=tk.LEFT, padx=(10, 0))

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(
            button_frame,
            text="保存",
            command=self.save_voice,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="取消",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="测试播放",
            command=self.test_play_audio,
            state="normal" if self.ref_path_var.get() and os.path.exists(self.ref_path_var.get()) else "disabled"
        ).pack(side=tk.LEFT, padx=5)

        # 配置列权重
        main_frame.columnconfigure(1, weight=1)

    def on_path_changed(self, *args):
        """路径改变时更新预览按钮状态"""
        path = self.ref_path_var.get()

        if path and os.path.exists(path):
            # 更新预览按钮状态
            if self.is_playing and self.current_playing_path == path:
                self.preview_btn.configure(text="⏹ 停止", state="normal")
                self.preview_status_var.set("正在播放...")
            else:
                self.preview_btn.configure(text="▶ 预览播放", state="normal")
                self.preview_status_var.set("点击预览播放")

            # 显示文件信息
            try:
                file_size = os.path.getsize(path)
                file_size_mb = file_size / (1024 * 1024)
                file_info = f"文件大小: {file_size_mb:.2f} MB"

                # 检查文件格式
                if path.lower().endswith('.wav'):
                    file_info += " | 格式: WAV"
                elif path.lower().endswith('.mp3'):
                    file_info += " | 格式: MP3"
                else:
                    file_info += " | 格式: 其他"

                self.file_info_var.set(file_info)

            except Exception as e:
                self.file_info_var.set(f"文件信息获取失败: {e}")

        else:
            # 文件不存在或路径为空
            self.preview_btn.configure(text="▶ 预览播放", state="disabled")
            self.preview_status_var.set("请选择有效的音频文件")
            self.file_info_var.set("")

            if path and not os.path.exists(path):
                self.preview_status_var.set("文件不存在")

    def on_multi_emotion_changed(self):
        """多情绪音色选择改变"""
        if self.multi_emotion_var.get():
            self.emotion_tip_var.set("✓ 已启用多情绪音色")
        else:
            self.emotion_tip_var.set("启用后可为不同情绪配置不同音频")

    def browse_audio_file(self):
        """浏览音频文件"""
        filename = filedialog.askopenfilename(
            title="选择参考音频文件",
            filetypes=[
                ("音频文件", "*.wav *.mp3 *.ogg *.flac"),
                ("WAV文件", "*.wav"),
                ("MP3文件", "*.mp3"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.ref_path_var.set(filename)

    def toggle_preview_audio(self):
        """切换音频预览播放/停止"""
        path = self.ref_path_var.get()
        if not path or not os.path.exists(path):
            messagebox.showwarning("警告", "请先选择有效的音频文件")
            return

        if self.is_playing and self.current_playing_path == path:
            # 正在播放，点击停止
            self.stop_audio_playback()
            self.preview_btn.configure(text="▶ 预览播放")
            self.preview_status_var.set("播放已停止")
        else:
            # 开始播放
            if self.play_audio(path):
                self.preview_btn.configure(text="⏹ 停止")
                self.preview_status_var.set("正在播放...")
                # 启动播放监控
                self.start_playback_monitor(path)
            else:
                messagebox.showerror("错误", "播放音频失败")

    def test_play_audio(self):
        """测试播放音频（与预览播放相同）"""
        self.toggle_preview_audio()

    def play_audio(self, file_path: str) -> bool:
        """播放音频文件 - 使用内置播放器"""
        try:
            # 停止当前播放（如果有）
            if self.is_playing:
                self.stop_audio_playback()

            # 使用内置音频播放器
            success = audio_player.play_audio(file_path)
            if success:
                self.is_playing = True
                self.current_playing_path = file_path
                return True
            else:
                return False

        except Exception as e:
            print(f"播放音频失败: {e}")
            return False

    def start_playback_monitor(self, file_path: str):
        """启动播放监控"""

        def monitor():
            while audio_player.is_playing and self.is_playing and self.current_playing_path == file_path:
                time.sleep(0.1)

            # 播放结束或被停止
            if self.is_playing and self.current_playing_path == file_path:
                self.dialog.after(0, self.on_playback_finished)

        self.play_thread = threading.Thread(target=monitor, daemon=True)
        self.play_thread.start()

    def stop_audio_playback(self):
        """停止音频播放"""
        audio_player.stop_audio()
        self.is_playing = False
        self.current_playing_path = None

    def on_playback_finished(self):
        """播放结束回调"""
        self.preview_btn.configure(text="▶ 预览播放")
        self.preview_status_var.set("播放完成")
        self.is_playing = False
        self.current_playing_path = None
        # 2秒后恢复默认状态
        self.dialog.after(2000, lambda: self.preview_status_var.set("点击预览播放"))

    def save_voice(self):
        """保存音色"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("错误", "音色名称不能为空")
            return

        description = self.desc_text.get('1.0', tk.END).strip()
        reference_path = self.ref_path_var.get().strip() or None
        is_multi_emotion = 1 if self.multi_emotion_var.get() else 0

        # 验证参考音频文件是否存在（如果提供了路径）
        if reference_path and not os.path.exists(reference_path):
            if not messagebox.askyesno("警告", "参考音频文件不存在，是否继续保存？"):
                return

        try:
            if self.voice:
                # 更新现有音色
                update_data = {
                    'name': name,
                    'description': description,
                    'reference_path': reference_path,
                    'is_multi_emotion': is_multi_emotion
                }
                success = self.app_controller.voice_controller.update_voice(
                    self.voice.id,
                    **update_data
                )
            else:
                # 创建新音色
                voice = self.app_controller.voice_controller.create_voice(
                    tts_provider_id=self.tts_provider_id,
                    name=name,
                    reference_path=reference_path,
                    description=description,
                    is_multi_emotion=is_multi_emotion
                )
                success = voice is not None

            if success:
                self.result = True
                # 停止播放（如果有）
                if self.is_playing:
                    self.stop_audio_playback()
                self.dialog.destroy()
            else:
                messagebox.showerror("错误", "保存音色失败")

        except Exception as e:
            messagebox.showerror("错误", f"保存音色失败: {str(e)}")

    def __del__(self):
        """析构函数，确保停止播放"""
        if self.is_playing:
            self.stop_audio_playback()
