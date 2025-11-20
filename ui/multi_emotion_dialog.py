# app/ui/multi_emotion_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List

from app.entity.voice_entity import VoiceEntity
from app.entity.multi_emotion_voice_entity import MultiEmotionVoiceEntity


class MultiEmotionDialog:
    def __init__(self, parent, voice: VoiceEntity, app_controller):
        self.parent = parent
        self.voice = voice
        self.app_controller = app_controller
        self.multi_emotion_voices: List[MultiEmotionVoiceEntity] = []

        self.setup_dialog()
        self.load_data()

    def setup_dialog(self):
        """设置对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f"管理多情绪音色 - {self.voice.name}")
        self.dialog.geometry("800x600")
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

        # 情绪音色列表
        list_frame = ttk.LabelFrame(main_frame, text="情绪音色列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建树形视图
        columns = ("emotion", "strength", "reference_path")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=15
        )

        self.tree.heading("emotion", text="情绪")
        self.tree.heading("strength", text="强度")
        self.tree.heading("reference_path", text="参考音频路径")

        self.tree.column("emotion", width=100)
        self.tree.column("strength", width=100)
        self.tree.column("reference_path", width=300)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="添加情绪", command=self.add_emotion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑", command=self.edit_emotion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除", command=self.delete_emotion).pack(side=tk.LEFT, padx=5)

    def load_data(self):
        """加载多情绪音色数据"""
        try:
            self.multi_emotion_voices = self.app_controller.multi_emotion_voice_controller.get_multi_emotion_voices_by_voice(
                self.voice.id
            )
            self.refresh_treeview()
        except Exception as e:
            messagebox.showerror("错误", f"加载多情绪音色失败: {str(e)}")

    def refresh_treeview(self):
        """刷新树形视图"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for me_voice in self.multi_emotion_voices:
            # 这里需要获取情绪和强度的名称，需要相应的服务方法
            emotion_name = f"情绪{me_voice.emotion_id}"  # 需要根据实际情况获取
            strength_name = f"强度{me_voice.strength_id}"  # 需要根据实际情况获取

            self.tree.insert(
                "",
                tk.END,
                values=(
                    emotion_name,
                    strength_name,
                    me_voice.reference_path or ""
                ),
                tags=(me_voice.id,)
            )

    def add_emotion(self):
        """添加情绪音色"""
        messagebox.showinfo("提示", "添加情绪音色功能待实现")

    def edit_emotion(self):
        """编辑情绪音色"""
        messagebox.showinfo("提示", "编辑情绪音色功能待实现")

    def delete_emotion(self):
        """删除情绪音色"""
        messagebox.showinfo("提示", "删除情绪音色功能待实现")