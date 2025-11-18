# app/ui/role_editor.py
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Optional

from app.entity.role_entity import RoleEntity
from app.entity.voice_entity import VoiceEntity


class RoleEditor(ttk.Frame):
    def __init__(self, parent, current_project, app_controller):
        super().__init__(parent)
        self.parent = parent
        self.current_project = current_project
        self.app_controller = app_controller

        self.roles: List[RoleEntity] = []
        self.voices: List[VoiceEntity] = []

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """设置角色库界面"""
        # 创建主框架
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 顶部工具栏
        toolbar_frame = ttk.Frame(main_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        # 搜索框
        ttk.Label(toolbar_frame, text="搜索角色:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', self.on_search)

        # 按钮
        ttk.Button(toolbar_frame, text="管理员仓库", command=self.open_voice_manager).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="新建角色", command=self.create_role).pack(side=tk.LEFT, padx=5)

        # 角色列表框架
        list_frame = ttk.LabelFrame(main_frame, text="角色列表")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 创建树形视图显示角色
        columns = ("name", "voice", "created_at")
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            height=15
        )

        # 设置列
        self.tree.heading("name", text="角色名称")
        self.tree.heading("voice", text="绑定音色")
        self.tree.heading("created_at", text="创建时间")

        self.tree.column("name", width=150)
        self.tree.column("voice", width=150)
        self.tree.column("created_at", width=200)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定双击事件
        self.tree.bind('<Double-1>', self.on_item_double_click)

    def load_data(self):
        """加载角色和音色数据"""
        if not self.current_project:
            return

        try:
            # 加载角色列表 - 使用控制器的方法
            self.roles = self.app_controller.role_controller.get_roles_by_project(
                self.current_project.id
            )

            # 加载音色列表（假设使用默认的TTS供应商）
            self.voices = self.app_controller.voice_controller.get_voices_by_tts_provider(tts_provider_id=1)

            self.refresh_treeview()

        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")

    def refresh_treeview(self):
        """刷新树形视图"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 添加角色数据
        for role in self.roles:
            # 查找绑定的音色名称
            voice_name = "未绑定音色"
            if role.default_voice_id:
                voice = next((v for v in self.voices if v.id == role.default_voice_id), None)
                if voice:
                    voice_name = voice.name

            # 格式化创建时间
            created_time = role.created_at.strftime("%Y-%m-%d %H:%M:%S") if role.created_at else "未知"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    role.name,
                    voice_name,
                    created_time
                ),
                tags=(role.id,)
            )

    def on_search(self, event):
        """搜索角色"""
        search_text = self.search_var.get().lower()

        # 清空现有显示
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 过滤并显示匹配的角色
        for role in self.roles:
            if search_text in role.name.lower():
                voice_name = "未绑定音色"
                if role.default_voice_id:
                    voice = next((v for v in self.voices if v.id == role.default_voice_id), None)
                    if voice:
                        voice_name = voice.name

                created_time = role.created_at.strftime("%Y-%m-%d %H:%M:%S") if role.created_at else "未知"

                self.tree.insert(
                    "",
                    tk.END,
                    values=(
                        role.name,
                        voice_name,
                        created_time
                    ),
                    tags=(role.id,)
                )

    def on_item_double_click(self, event):
        """双击编辑角色"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        role_id = self.tree.item(item, "tags")[0]

        role = next((r for r in self.roles if r.id == role_id), None)
        if role:
            self.edit_role(role)

    def create_role(self):
        """创建新角色"""
        from app.ui.role_dialog import RoleDialog

        dialog = RoleDialog(
            self,
            self.current_project,
            self.app_controller,
            self.voices
        )
        self.wait_window(dialog.dialog)

        if dialog.result:
            self.load_data()  # 刷新数据

    def edit_role(self, role):
        """编辑角色"""
        from app.ui.role_dialog import RoleDialog

        dialog = RoleDialog(
            self,
            self.current_project,
            self.app_controller,
            self.voices,
            role
        )
        self.wait_window(dialog.dialog)

        if dialog.result:
            self.load_data()  # 刷新数据

    def open_voice_manager(self):
        """打开音色管理器"""
        messagebox.showinfo("提示", "音色管理功能待实现")