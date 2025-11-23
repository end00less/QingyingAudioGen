# app/ui/voice_selector_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import os

from app.entity.voice_entity import VoiceEntity
from app.entity.tts_provider_entity import TTSProviderEntity
from app.services.audio_player_service import audio_player


class VoiceSelectorDialog:
    def __init__(self, parent, app_controller, current_voice: Optional[VoiceEntity] = None):
        self.parent = parent
        self.app_controller = app_controller
        self.current_voice = current_voice
        self.result = None
        self.selected_voice = None

        self.voices: List[VoiceEntity] = []
        self.tts_providers: List[TTSProviderEntity] = []
        self.filtered_voices: List[VoiceEntity] = []
        self.current_tts_provider_id: Optional[int] = None

        # 存储播放按钮状态
        self.play_buttons = {}  # voice_id -> button
        self.is_playing = False
        self.current_playing_voice_id = None

        self.setup_dialog()

    def setup_dialog(self):
        """设置对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("选择音色")
        self.dialog.geometry("800x600")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        """创建控件"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部筛选工具栏
        filter_frame = ttk.LabelFrame(main_frame, text="筛选条件", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # TTS服务商选择
        ttk.Label(filter_frame, text="TTS服务商:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.tts_provider_var = tk.StringVar()
        self.tts_provider_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.tts_provider_var,
            width=15,
            state="readonly"
        )
        self.tts_provider_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        self.tts_provider_combo.bind('<<ComboboxSelected>>', self.on_tts_provider_changed)

        # 搜索框
        ttk.Label(filter_frame, text="搜索音色:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_frame, textvariable=self.search_var, width=20)
        self.search_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 20))
        self.search_entry.bind('<KeyRelease>', self.on_search)

        # 多情绪音色筛选
        self.multi_emotion_var = tk.BooleanVar()
        ttk.Checkbutton(
            filter_frame,
            text="仅显示多情绪音色",
            variable=self.multi_emotion_var,
            command=self.on_filter_changed
        ).grid(row=0, column=4, sticky=tk.W)

        # 配置网格权重
        filter_frame.columnconfigure(3, weight=1)

        # 音色列表框架
        list_frame = ttk.LabelFrame(main_frame, text="音色列表")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建树形视图显示音色
        columns = ("name", "description", "multi_emotion", "has_sample")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # 设置列
        self.tree.heading("name", text="音色名称")
        self.tree.heading("description", text="描述")
        self.tree.heading("multi_emotion", text="多情绪")
        self.tree.heading("has_sample", text="有样本")

        self.tree.column("name", width=150)
        self.tree.column("description", width=200)
        self.tree.column("multi_emotion", width=80)
        self.tree.column("has_sample", width=80)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定选择事件
        self.tree.bind('<<TreeviewSelect>>', self.on_selection_changed)
        self.tree.bind('<Double-1>', self.on_double_click)

        # 操作按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        # 左侧按钮
        left_btn_frame = ttk.Frame(button_frame)
        left_btn_frame.pack(side=tk.LEFT)

        self.play_btn = ttk.Button(
            left_btn_frame,
            text="▶ 试听",
            command=self.play_selected_voice,
            state="disabled"
        )
        self.play_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            left_btn_frame,
            text="刷新",
            command=self.load_data
        ).pack(side=tk.LEFT, padx=5)

        # 右侧按钮
        right_btn_frame = ttk.Frame(button_frame)
        right_btn_frame.pack(side=tk.RIGHT)

        ttk.Button(
            right_btn_frame,
            text="取消绑定",
            command=self.cancel_selection
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            right_btn_frame,
            text="确定",
            command=self.confirm_selection,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            right_btn_frame,
            text="取消",
            command=self.dialog.destroy
        ).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """加载数据"""
        try:
            # 加载TTS服务商
            self.tts_providers = self.app_controller.tts_provider_controller.get_all_tts_providers()
            provider_names = [p.name for p in self.tts_providers]
            self.tts_provider_combo['values'] = provider_names

            if provider_names:
                self.tts_provider_combo.set(provider_names[0])
                self.current_tts_provider_id = self.tts_providers[0].id

            # 加载音色
            self.refresh_voices()

        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")

    def refresh_voices(self):
        """刷新音色显示"""
        if not self.current_tts_provider_id:
            return

        try:
            # 获取当前TTS服务商的音色
            self.voices = self.app_controller.voice_controller.get_voices_by_tts_provider(
                self.current_tts_provider_id
            )

            # 应用筛选
            self.apply_filters()

            # 更新显示
            self.update_treeview()

        except Exception as e:
            messagebox.showerror("错误", f"加载音色失败: {str(e)}")

    def apply_filters(self):
        """应用筛选条件"""
        self.filtered_voices = self.voices.copy()

        # 搜索筛选
        search_text = self.search_var.get().lower()
        if search_text:
            self.filtered_voices = [
                v for v in self.filtered_voices
                if search_text in v.name.lower() or
                   (v.description and search_text in v.description.lower())
            ]

        # 多情绪音色筛选
        if self.multi_emotion_var.get():
            self.filtered_voices = [v for v in self.filtered_voices if v.is_multi_emotion == 1]

    def update_treeview(self):
        """更新树形视图"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 添加音色数据
        for voice in self.filtered_voices:
            description = voice.description[:30] + "..." if voice.description and len(voice.description) > 30 else (
                        voice.description or "")
            multi_emotion = "是" if voice.is_multi_emotion else "否"
            has_sample = "✅" if voice.reference_path and os.path.exists(voice.reference_path) else "❌"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    voice.name,
                    description,
                    multi_emotion,
                    has_sample
                ),
                tags=(str(voice.id),)  # 确保存储为字符串
            )

        # 自动选中当前音色
        if self.current_voice:
            for item in self.tree.get_children():
                voice_id_str = self.tree.item(item, "tags")[0]
                if voice_id_str == str(self.current_voice.id):  # 两边都转为字符串比较
                    self.tree.selection_set(item)
                    self.tree.see(item)
                    break

    def on_selection_changed(self, event):
        """选择改变事件"""
        selection = self.tree.selection()
        if selection:
            self.play_btn.configure(state="normal")
        else:
            self.play_btn.configure(state="disabled")

    def on_double_click(self, event):
        """双击确认选择"""
        self.confirm_selection()

    def play_selected_voice(self):
        """试听选中的音色"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个音色")
            return

        item = selection[0]
        tags = self.tree.item(item, "tags")
        voice_id_str = tags[0] if tags else None

        # 将字符串转换为整数
        try:
            voice_id = int(voice_id_str) if voice_id_str else None
        except (ValueError, TypeError):
            voice_id = None

        print(f"试听调试: voice_id_str={voice_id_str}, voice_id={voice_id}")

        voice = next((v for v in self.filtered_voices if v.id == voice_id), None)
        print(f"试听调试: 找到的音色={voice}")

        if not voice:
            messagebox.showerror("错误", "未找到对应的音色")
            return

        if not voice.reference_path:
            messagebox.showwarning("警告", "该音色没有样本文件")
            return

        if not os.path.exists(voice.reference_path):
            messagebox.showwarning("警告", f"样本文件不存在: {voice.reference_path}")
            return

        try:
            if self.is_playing and self.current_playing_voice_id == voice_id:
                # 停止播放
                audio_player.stop_audio()
                self.play_btn.configure(text="▶ 试听")
                self.is_playing = False
                self.current_playing_voice_id = None
            else:
                # 开始播放
                if audio_player.play_audio(voice.reference_path):
                    self.play_btn.configure(text="⏹ 停止")
                    self.is_playing = True
                    self.current_playing_voice_id = voice_id

                    # 启动播放监控
                    self.monitor_playback(voice_id)
                else:
                    messagebox.showerror("错误", "播放失败")

        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {str(e)}")

    def monitor_playback(self, voice_id: int):
        """监控播放状态"""

        def check_playback():
            # 检查播放状态
            if hasattr(audio_player, 'is_playing'):
                is_playing = audio_player.is_playing
            else:
                # 如果 audio_player 没有 is_playing 属性，使用其他方式判断
                is_playing = self.is_playing  # 回退到自己的状态

            if is_playing and self.is_playing and self.current_playing_voice_id == voice_id:
                self.dialog.after(100, check_playback)
                return

            # 播放结束
            if self.is_playing and self.current_playing_voice_id == voice_id:
                self.play_btn.configure(text="▶ 试听")
                self.is_playing = False
                self.current_playing_voice_id = None

        self.dialog.after(100, check_playback)

    def on_tts_provider_changed(self, event):
        """TTS服务商改变事件"""
        provider_name = self.tts_provider_var.get()
        provider = next((p for p in self.tts_providers if p.name == provider_name), None)
        if provider:
            self.current_tts_provider_id = provider.id
            self.refresh_voices()

    def on_search(self, event):
        """搜索事件"""
        self.apply_filters()
        self.update_treeview()

    def on_filter_changed(self):
        """筛选条件改变事件"""
        self.apply_filters()
        self.update_treeview()

    def confirm_selection(self):
        """确认选择"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            tags = self.tree.item(item, "tags")
            voice_id_str = tags[0] if tags else None

            # 将字符串转换为整数
            try:
                voice_id = int(voice_id_str) if voice_id_str else None
            except (ValueError, TypeError):
                voice_id = None

            self.selected_voice = next((v for v in self.filtered_voices if v.id == voice_id), None)
            self.result = True
            self.dialog.destroy()
        else:
            messagebox.showwarning("警告", "请先选择一个音色")

    def cancel_selection(self):
        """取消选择（设置为未绑定）"""
        self.selected_voice = None
        self.result = True
        self.dialog.destroy()
