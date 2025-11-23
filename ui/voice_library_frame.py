# app/ui/voice_library_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import os
import threading
import time

from app.entity.voice_entity import VoiceEntity
from app.entity.tts_provider_entity import TTSProviderEntity
from app.services.audio_player_service import audio_player


class VoiceLibraryFrame(ttk.Frame):
    def __init__(self, parent, current_project, app_controller):
        super().__init__(parent)
        self.parent = parent  # 添加 parent 引用
        self.current_project = current_project
        self.app_controller = app_controller

        self.voices: List[VoiceEntity] = []
        self.tts_providers: List[TTSProviderEntity] = []
        self.filtered_voices: List[VoiceEntity] = []
        self.current_tts_provider_id: Optional[int] = None

        # 存储播放按钮状态
        self.play_buttons = {}  # voice_id -> button
        self.current_playing_voice_id = None
        self.play_thread = None

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """设置音色库界面"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部筛选工具栏
        self.create_filter_toolbar(main_frame)

        # 音色网格显示区域
        self.create_voice_grid(main_frame)

        # 底部操作栏
        self.create_bottom_toolbar(main_frame)

    def create_filter_toolbar(self, parent):
        """创建筛选工具栏"""
        filter_frame = ttk.LabelFrame(parent, text="筛选条件", padding="10")
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

    def create_voice_grid(self, parent):
        """创建音色网格显示区域"""
        # 创建滚动框架
        grid_frame = ttk.Frame(parent)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        # 创建画布和滚动条
        self.canvas = tk.Canvas(grid_frame, bg='white')
        scrollbar = ttk.Scrollbar(grid_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_bottom_toolbar(self, parent):
        """创建底部操作栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            toolbar_frame,
            text="新建音色",
            command=self.create_voice
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            toolbar_frame,
            text="刷新",
            command=self.load_data
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            toolbar_frame,
            text="导入音色",
            command=self.import_voice
        ).pack(side=tk.LEFT, padx=5)

        # 全局停止按钮
        ttk.Button(
            toolbar_frame,
            text="停止所有播放",
            command=self.stop_all_playback,
            style="Accent.TButton"
        ).pack(side=tk.RIGHT, padx=5)

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
        # 清空播放按钮引用
        self.play_buttons.clear()

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
            self.update_voice_grid()

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

    def update_voice_grid(self):
        """更新音色网格显示"""
        # 清空现有内容
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.filtered_voices:
            # 显示空状态
            empty_frame = ttk.Frame(self.scrollable_frame)
            empty_frame.pack(expand=True, pady=50)

            ttk.Label(
                empty_frame,
                text="🎵 暂无音色数据",
                font=("Arial", 14)
            ).pack(pady=5)

            ttk.Label(
                empty_frame,
                text="点击'新建音色'按钮添加第一个音色",
                font=("Arial", 10),
                foreground="gray"
            ).pack()
            return

        # 创建音色卡片网格
        row, col = 0, 0
        max_cols = 4  # 每行最多显示4个音色

        for voice in self.filtered_voices:
            voice_card = self.create_voice_card(voice)
            voice_card.grid(
                row=row,
                column=col,
                padx=10,
                pady=10,
                sticky="nsew"
            )

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # 配置网格权重
        for i in range(max_cols):
            self.scrollable_frame.columnconfigure(i, weight=1)
        for i in range(row + 1):
            self.scrollable_frame.rowconfigure(i, weight=1)

    def create_voice_card(self, voice: VoiceEntity) -> ttk.Frame:
        """创建音色卡片"""
        card_frame = ttk.LabelFrame(self.scrollable_frame, text=voice.name, padding="10")
        card_frame.configure(width=220, height=180)

        # 音色信息
        info_text = f"名称: {voice.name}\n"
        if voice.description:
            desc = voice.description[:20] + "..." if len(voice.description) > 20 else voice.description
            info_text += f"描述: {desc}\n"
        info_text += f"多情绪: {'是' if voice.is_multi_emotion else '否'}\n"

        # 检查样本文件状态
        has_sample = voice.reference_path and os.path.exists(voice.reference_path)
        if has_sample:
            info_text += "✅ 有样本"
        else:
            info_text += "❌ 无样本"

        info_label = ttk.Label(card_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W, pady=(0, 10))

        # 操作按钮框架
        btn_frame = ttk.Frame(card_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        # 播放/停止按钮
        play_btn_text = "⏹ 停止" if self.current_playing_voice_id == voice.id else "▶ 播放"
        play_btn = ttk.Button(
            btn_frame,
            text=play_btn_text,
            command=lambda v=voice: self.toggle_play_audio(v),
            width=8,
            state="normal" if has_sample else "disabled"
        )
        play_btn.pack(side=tk.LEFT, padx=2)

        # 存储播放按钮引用
        self.play_buttons[voice.id] = play_btn

        # 编辑按钮
        ttk.Button(
            btn_frame,
            text="编辑",
            command=lambda v=voice: self.edit_voice(v),
            width=6
        ).pack(side=tk.LEFT, padx=2)

        # 删除按钮
        ttk.Button(
            btn_frame,
            text="删除",
            command=lambda v=voice: self.delete_voice(v),
            width=6
        ).pack(side=tk.LEFT, padx=2)

        # 如果是多情绪音色，添加情绪管理按钮
        if voice.is_multi_emotion:
            ttk.Button(
                btn_frame,
                text="情绪",
                command=lambda v=voice: self.manage_emotions(v),
                width=6
            ).pack(side=tk.LEFT, padx=2)

        return card_frame

    def toggle_play_audio(self, voice: VoiceEntity):
        """切换音频播放/停止"""
        if not voice.reference_path or not os.path.exists(voice.reference_path):
            messagebox.showwarning("警告", f"音色 {voice.name} 没有可用的样本文件")
            return

        play_btn = self.play_buttons.get(voice.id)
        if not play_btn:
            return

        if self.current_playing_voice_id == voice.id and audio_player.is_playing:
            # 正在播放这个文件，点击停止
            self.stop_audio_playback()
            play_btn.configure(text="▶ 播放")
            self.current_playing_voice_id = None
        else:
            # 停止当前播放（如果有）
            if audio_player.is_playing:
                self.stop_audio_playback()
                # 更新之前播放的按钮
                if self.current_playing_voice_id:
                    prev_btn = self.play_buttons.get(self.current_playing_voice_id)
                    if prev_btn:
                        prev_btn.configure(text="▶ 播放")

            # 开始播放新文件
            if self.play_audio(voice):
                play_btn.configure(text="⏹ 停止")
                self.current_playing_voice_id = voice.id
                # 启动播放监控
                self.start_playback_monitor(voice)
            else:
                messagebox.showerror("错误", f"播放音频失败: {voice.reference_path}")

    def play_audio(self, voice: VoiceEntity) -> bool:
        """播放音频文件 - 使用内置播放器"""
        try:
            # 使用内置音频播放器
            success = audio_player.play_audio(voice.reference_path)
            return success

        except Exception as e:
            print(f"播放音频失败: {e}")
            return False

    def start_playback_monitor(self, voice: VoiceEntity):
        """启动播放监控"""

        def monitor():
            while audio_player.is_playing and self.current_playing_voice_id == voice.id:
                time.sleep(0.1)

            # 播放结束或被停止
            if self.current_playing_voice_id == voice.id:
                self.after(0, lambda: self.update_play_button(voice.id, "▶ 播放"))
                self.current_playing_voice_id = None

        self.play_thread = threading.Thread(target=monitor, daemon=True)
        self.play_thread.start()

    def stop_audio_playback(self):
        """停止音频播放"""
        audio_player.stop_audio()
        self.current_playing_voice_id = None

    def stop_all_playback(self):
        """停止所有播放"""
        if audio_player.is_playing:
            self.stop_audio_playback()
            # 更新所有播放按钮
            for voice_id, play_btn in self.play_buttons.items():
                play_btn.configure(text="▶ 播放")
            messagebox.showinfo("提示", "已停止所有音频播放")

    def update_play_button(self, voice_id: int, text: str):
        """更新播放按钮文本"""
        play_btn = self.play_buttons.get(voice_id)
        if play_btn and play_btn.winfo_exists():
            play_btn.configure(text=text)

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
        self.update_voice_grid()

    def on_filter_changed(self):
        """筛选条件改变事件"""
        self.apply_filters()
        self.update_voice_grid()

    def create_voice(self):
        """创建新音色"""
        from app.ui.voice_dialog import VoiceDialog

        if not self.current_tts_provider_id:
            messagebox.showwarning("警告", "请先选择TTS服务商")
            return

        dialog = VoiceDialog(
            self.parent,  # 使用 self.parent 而不是 self
            self.current_tts_provider_id,
            self.app_controller
        )
        # 修复：使用 self.parent.wait_window 而不是 self.wait_window
        self.parent.wait_window(dialog.dialog)

        if dialog.result:
            self.refresh_voices()

    def edit_voice(self, voice: VoiceEntity):
        """编辑音色"""
        from app.ui.voice_dialog import VoiceDialog

        dialog = VoiceDialog(
            self.parent,  # 使用 self.parent 而不是 self
            self.current_tts_provider_id,
            self.app_controller,
            voice
        )
        # 修复：使用 self.parent.wait_window 而不是 self.wait_window
        self.parent.wait_window(dialog.dialog)

        if dialog.result:
            self.refresh_voices()

    def delete_voice(self, voice: VoiceEntity):
        """删除音色"""
        if not messagebox.askyesno("确认删除", f"确定要删除音色 '{voice.name}' 吗？"):
            return

        try:
            success = self.app_controller.voice_controller.delete_voice(voice.id)
            if success:
                messagebox.showinfo("成功", f"音色 '{voice.name}' 删除成功")
                self.refresh_voices()
            else:
                messagebox.showerror("错误", "删除音色失败")
        except Exception as e:
            messagebox.showerror("错误", f"删除音色失败: {str(e)}")

    def manage_emotions(self, voice: VoiceEntity):
        """管理多情绪音色"""
        from app.ui.multi_emotion_dialog import MultiEmotionDialog

        dialog = MultiEmotionDialog(
            self.parent,  # 使用 self.parent 而不是 self
            voice,
            self.app_controller
        )
        # 修复：使用 self.parent.wait_window 而不是 self.wait_window
        self.parent.wait_window(dialog.dialog)

    def import_voice(self):
        """导入音色"""
        messagebox.showinfo("提示", "音色导入功能待实现")
