# app/ui/character_dialog.py
import tkinter as tk
from tkinter import ttk
from typing import List, Optional

from app.entity.character_entity import CharacterEntity
from app.entity.voice_entity import VoiceEntity


class CharacterDialog:
    def __init__(self, parent, current_project, app_controller, voices: List[VoiceEntity],
                 character: Optional[CharacterEntity] = None):
        self.parent = parent
        self.current_project = current_project
        self.app_controller = app_controller
        self.voices = voices
        self.character = character
        self.result = None

        self.setup_dialog()

    def setup_dialog(self):
        """设置对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑角色" if self.character else "新建角色")
        self.dialog.geometry("500x400")
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

        # 角色名称
        ttk.Label(main_frame, text="角色名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        if self.character:
            self.name_var.set(self.character.name)
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 绑定音色
        ttk.Label(main_frame, text="绑定音色:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(main_frame, textvariable=self.voice_var, width=27)

        # 设置音色选项
        voice_names = ["未绑定音色"] + [voice.name for voice in self.voices]
        self.voice_combo['values'] = voice_names
        self.voice_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 如果编辑现有角色，设置当前音色
        if self.character and self.character.voice_id:
            voice = next((v for v in self.voices if v.id == self.character.voice_id), None)
            if voice:
                self.voice_var.set(voice.name)
            else:
                self.voice_var.set("未绑定音色")
        else:
            self.voice_var.set("未绑定音色")

        # 角色描述
        ttk.Label(main_frame, text="角色描述:").grid(row=2, column=0, sticky=tk.NW, pady=5)
        self.desc_text = tk.Text(main_frame, width=30, height=10)
        self.desc_text.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        if self.character and self.character.description:
            self.desc_text.insert('1.0', self.character.description)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="保存", command=self.save_character).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

    def save_character(self):
        """保存角色"""
        name = self.name_var.get().strip()
        if not name:
            tk.messagebox.showerror("错误", "角色名称不能为空")
            return

        # 获取选中的音色ID
        voice_id = None
        selected_voice = self.voice_var.get()
        if selected_voice != "未绑定音色":
            voice = next((v for v in self.voices if v.name == selected_voice), None)
            if voice:
                voice_id = voice.id

        description = self.desc_text.get('1.0', tk.END).strip()

        try:
            if self.character:
                # 更新现有角色
                self.character.name = name
                self.character.voice_id = voice_id
                self.character.description = description
                success = self.app_controller.character_controller.update_character(self.character)
            else:
                # 创建新角色
                character_data = {
                    'name': name,
                    'voice_id': voice_id,
                    'description': description,
                    'project_id': self.current_project.id
                }
                success = self.app_controller.character_controller.create_character(character_data)

            if success:
                self.result = True
                self.dialog.destroy()
            else:
                tk.messagebox.showerror("错误", "保存角色失败")

        except Exception as e:
            tk.messagebox.showerror("错误", f"保存角色失败: {str(e)}")