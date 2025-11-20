# app/ui/voice_library_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional
import os

from app.entity.voice_entity import VoiceEntity
from app.entity.tts_provider_entity import TTSProviderEntity


class VoiceLibraryFrame(ttk.Frame):
    def __init__(self, parent, current_project, app_controller):
        super().__init__(parent)
        self.parent = parent
        self.current_project = current_project
        self.app_controller = app_controller

        self.voices: List[VoiceEntity] = []
        self.tts_providers: List[TTSProviderEntity] = []
        self.filtered_voices: List[VoiceEntity] = []
        self.current_tts_provider_id: Optional[int] = None

        # 存储播放按钮状态
        self.play_buttons = {}  # voice_id -> button

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

    # 在voice_library_frame.py的load_data方法中
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

                # 自动初始化默认音色（如果音色库为空）
                voices = self.app_controller.voice_controller.get_voices_by_tts_provider(self.current_tts_provider_id)
                if not voices:
                    print("音色库为空，正在初始化默认音色...")
                    self.app_controller.voice_controller.initialize_default_voices(self.current_tts_provider_id)

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
            ttk.Label(
                self.scrollable_frame,
                text="暂无音色数据",
                font=("Arial", 12)
            ).pack(expand=True, pady=50)
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
        card_frame.configure(width=200, height=150)

        # 音色信息
        info_text = f"名称: {voice.name}\n"
        if voice.description:
            info_text += f"描述: {voice.description}\n"
        info_text += f"多情绪: {'是' if voice.is_multi_emotion else '否'}"

        ttk.Label(card_frame, text=info_text, justify=tk.LEFT).pack(anchor=tk.W)

        # 操作按钮
        btn_frame = ttk.Frame(card_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="编辑",
            command=lambda v=voice: self.edit_voice(v),
            width=8
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            btn_frame,
            text="删除",
            command=lambda v=voice: self.delete_voice(v),
            width=8
        ).pack(side=tk.LEFT, padx=2)

        if voice.is_multi_emotion:
            ttk.Button(
                btn_frame,
                text="情绪管理",
                command=lambda v=voice: self.manage_emotions(v),
                width=8
            ).pack(side=tk.LEFT, padx=2)

        return card_frame

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
            self,
            self.current_tts_provider_id,
            self.app_controller
        )
        self.wait_window(dialog.dialog)

        if dialog.result:
            self.refresh_voices()

    def edit_voice(self, voice: VoiceEntity):
        """编辑音色"""
        from app.ui.voice_dialog import VoiceDialog

        dialog = VoiceDialog(
            self,
            self.current_tts_provider_id,
            self.app_controller,
            voice
        )
        self.wait_window(dialog.dialog)

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
            self,
            voice,
            self.app_controller
        )
        self.wait_window(dialog.dialog)

    def import_voice(self):
        """导入音色"""
        messagebox.showinfo("提示", "音色导入功能待实现")