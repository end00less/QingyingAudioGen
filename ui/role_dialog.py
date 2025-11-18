# app/ui/role_dialog.py
import tkinter as tk
from tkinter import ttk
from typing import List, Optional

from app.entity.role_entity import RoleEntity
from app.entity.voice_entity import VoiceEntity


class RoleDialog:
    def __init__(self, parent, current_project, app_controller, voices: List[VoiceEntity],
                 role: Optional[RoleEntity] = None):
        self.parent = parent
        self.current_project = current_project
        self.app_controller = app_controller
        self.voices = voices
        self.role = role
        self.result = None

        self.setup_dialog()

    def setup_dialog(self):
        """设置对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑角色" if self.role else "新建角色")
        self.dialog.geometry("400x200")
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
        ttk.Label(main_frame, text="角色名称:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.name_var = tk.StringVar()
        if self.role:
            self.name_var.set(self.role.name)
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=25)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        # 绑定音色
        ttk.Label(main_frame, text="绑定音色:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(main_frame, textvariable=self.voice_var, width=22, state="readonly")

        # 设置音色选项
        voice_names = ["未绑定音色"] + [voice.name for voice in self.voices]
        self.voice_combo['values'] = voice_names
        self.voice_combo.grid(row=1, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        # 如果编辑现有角色，设置当前音色
        if self.role and self.role.default_voice_id:
            voice = next((v for v in self.voices if v.id == self.role.default_voice_id), None)
            if voice:
                self.voice_var.set(voice.name)
            else:
                self.voice_var.set("未绑定音色")
        else:
            self.voice_var.set("未绑定音色")

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="保存", command=self.save_role).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

    def save_role(self):
        """保存角色"""
        name = self.name_var.get().strip()
        if not name:
            tk.messagebox.showerror("错误", "角色名称不能为空")
            return

        # 获取选中的音色ID
        default_voice_id = None
        selected_voice = self.voice_var.get()
        if selected_voice != "未绑定音色":
            voice = next((v for v in self.voices if v.name == selected_voice), None)
            if voice:
                default_voice_id = voice.id

        try:
            if self.role:
                # 更新现有角色 - 使用控制器的update_role方法
                update_data = {
                    'name': name,
                    'default_voice_id': default_voice_id
                }
                success = self.app_controller.role_controller.update_role(self.role.id, **update_data)
            else:
                # 创建新角色 - 使用控制器的create_role方法
                success = self.app_controller.role_controller.create_role(
                    project_id=self.current_project.id,
                    name=name,
                    default_voice_id=default_voice_id
                )

            if success:
                self.result = True
                self.dialog.destroy()
            else:
                tk.messagebox.showerror("错误", "保存角色失败")

        except Exception as e:
            tk.messagebox.showerror("错误", f"保存角色失败: {str(e)}")