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
        self.role_cards = {}  # 存储角色卡片的引用

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
        ttk.Button(toolbar_frame, text="管理音色库", command=self.open_voice_manager).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar_frame, text="新建角色", command=self.create_role).pack(side=tk.LEFT, padx=5)

        # 角色卡片区域
        self.create_card_area(main_frame)

    def create_card_area(self, parent):
        """创建卡片显示区域"""
        # 创建一个容器Frame来包含Canvas和Scrollbar
        container_frame = ttk.Frame(parent)
        container_frame.pack(fill=tk.BOTH, expand=True)

        # 创建滚动框架
        self.canvas = tk.Canvas(container_frame, bg="#f0f0f0", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # 绑定配置事件
        def on_frame_configure(event):
            # 更新Canvas的滚动区域
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            # 同步Canvas宽度与scrollable_frame宽度
            canvas_width = container_frame.winfo_width()
            if canvas_width > 1:  # 确保不是初始值
                # 减去滚动条宽度
                scrollbar_width = self.scrollbar.winfo_width()
                self.canvas.configure(width=canvas_width - scrollbar_width)

        def on_canvas_configure(event):
            # 当Canvas大小改变时，调整内部frame的宽度
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas.find_withtag("all")[0], width=canvas_width)
            self.scrollable_frame.configure(width=canvas_width)

        self.scrollable_frame.bind("<Configure>", on_frame_configure)
        self.canvas.bind("<Configure>", on_canvas_configure)

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=self.canvas.winfo_width())
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 使用grid布局，避免pack的左右分布问题
        container_frame.grid_rowconfigure(0, weight=1)
        container_frame.grid_columnconfigure(0, weight=1)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # 绑定鼠标滚轮事件
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")

        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)

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

            self.refresh_cards()

        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")

    def refresh_cards(self):
        """刷新角色卡片"""
        # 清空现有卡片
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.role_cards.clear()

        # 过滤角色
        search_text = self.search_var.get().lower()
        filtered_roles = [
            role for role in self.roles
            if search_text in role.name.lower()
        ]

        # 创建角色卡片
        for i, role in enumerate(filtered_roles):
            self.create_role_card(role, i)

    def create_role_card(self, role: RoleEntity, index: int):
        """创建角色卡片"""
        # 卡片框架
        card_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text="",
            padding="15"
        )

        # 使用grid布局，每行3个卡片
        row = index // 3
        col = index % 3
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # 配置列权重
        self.scrollable_frame.columnconfigure(col, weight=1)

        # 卡片内容
        self.create_card_content(card_frame, role)

        # 存储卡片引用
        self.role_cards[role.id] = card_frame

    def create_card_content(self, parent, role: RoleEntity):
        """创建卡片内容"""
        # 角色名称
        name_frame = ttk.Frame(parent)
        name_frame.pack(fill=tk.X, pady=(0, 10))

        name_label = ttk.Label(
            name_frame,
            text=role.name,
            font=("Arial", 12, "bold"),
            foreground="#2c3e50"
        )
        name_label.pack(anchor=tk.W)

        # 分隔线
        separator = ttk.Separator(parent, orient='horizontal')
        separator.pack(fill=tk.X, pady=5)

        # 音色信息
        voice_frame = ttk.Frame(parent)
        voice_frame.pack(fill=tk.X, pady=5)

        ttk.Label(voice_frame, text="绑定音色:", font=("Arial", 9)).pack(anchor=tk.W)

        # 查找绑定的音色
        voice_name = "未绑定"
        voice = None
        if role.default_voice_id:
            voice = next((v for v in self.voices if v.id == role.default_voice_id), None)
            if voice:
                voice_name = voice.name

        # 音色显示和按钮
        voice_info_frame = ttk.Frame(voice_frame)
        voice_info_frame.pack(fill=tk.X, pady=(2, 5))

        # 音色名称显示
        voice_display = ttk.Label(
            voice_info_frame,
            text=voice_name,
            font=("Arial", 10),
            foreground="#3498db" if voice else "#95a5a6",
            width=20
        )
        voice_display.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 绑定/更换音色按钮
        btn_text = "更换音色" if voice else "绑定音色"
        voice_btn = ttk.Button(
            voice_info_frame,
            text=btn_text,
            command=lambda r=role, v=voice: self.bind_voice(r, v),
            width=10
        )
        voice_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # 音色详细信息（如果有）
        if voice:
            info_text = ""
            if voice.description:
                info_text = f"描述: {voice.description[:30]}..."
            if voice.is_multi_emotion:
                info_text += (" | " if info_text else "") + "多情绪音色"

            if info_text:
                info_label = ttk.Label(
                    voice_frame,
                    text=info_text,
                    font=("Arial", 8),
                    foreground="#7f8c8d"
                )
                info_label.pack(anchor=tk.W, pady=(0, 5))

        # 创建时间
        if role.created_at:
            created_time = role.created_at.strftime("%Y-%m-%d %H:%M")
            time_label = ttk.Label(
                parent,
                text=f"创建时间: {created_time}",
                font=("Arial", 8),
                foreground="#95a5a6"
            )
            time_label.pack(anchor=tk.W, pady=(5, 10))

        # 操作按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # 编辑按钮
        edit_btn = ttk.Button(
            button_frame,
            text="编辑",
            command=lambda r=role: self.edit_role(r),
            width=8
        )
        edit_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 删除按钮
        delete_btn = ttk.Button(
            button_frame,
            text="删除",
            command=lambda r=role: self.delete_role(r),
            width=8
        )
        delete_btn.pack(side=tk.LEFT, padx=5)

        # 试听按钮（如果有音色）
        if voice and voice.reference_path:
            import os
            if os.path.exists(voice.reference_path):
                play_btn = ttk.Button(
                    button_frame,
                    text="▶ 试听",
                    command=lambda v=voice: self.play_voice(v),
                    width=8
                )
                play_btn.pack(side=tk.RIGHT)

    def bind_voice(self, role: RoleEntity, current_voice: Optional[VoiceEntity]):
        """绑定音色到角色"""
        from app.ui.voice_selector_dialog import VoiceSelectorDialog

        dialog = VoiceSelectorDialog(
            self,
            self.app_controller,
            current_voice
        )
        self.wait_window(dialog.dialog)

        if dialog.result:
            selected_voice = dialog.selected_voice
            try:
                # 确保传入的 name 和 project_id 与数据库中的完全一致
                update_data = {
                    'name': role.name,  # 使用角色当前的名称
                    'project_id': role.project_id,  # 使用角色当前的 project_id
                    'default_voice_id': selected_voice.id if selected_voice else None
                }

                # 调试信息
                print(f"调试信息:")
                print(f"  角色 ID: {role.id}")
                print(f"  角色名称: {role.name}")
                print(f"  角色项目ID: {role.project_id}")
                print(f"  当前项目ID: {self.current_project.id}")
                print(f"  选择的音色 ID: {selected_voice.id if selected_voice else 'None'}")
                print(f"  更新数据: {update_data}")

                success = self.app_controller.role_controller.update_role(role.id, **update_data)
                print(f"  更新结果: {success}")

                if success:
                    # 更新本地数据
                    role.default_voice_id = selected_voice.id if selected_voice else None

                    # 刷新显示
                    self.refresh_cards()
                    messagebox.showinfo("成功", f"已为角色 '{role.name}' 绑定音色")
                else:
                    messagebox.showerror("错误", "绑定音色失败，请检查角色名称是否唯一")

            except Exception as e:
                print(f"  异常信息: {str(e)}")
                messagebox.showerror("错误", f"绑定音色失败: {str(e)}")

    def play_voice(self, voice: VoiceEntity):
        """试听音色"""
        from app.services.audio_player_service import audio_player
        import os

        if voice.reference_path and os.path.exists(voice.reference_path):
            try:
                audio_player.play_audio(voice.reference_path)
            except Exception as e:
                messagebox.showerror("错误", f"播放失败: {str(e)}")
        else:
            messagebox.showwarning("警告", "音色文件不存在")

    def delete_role(self, role: RoleEntity):
        """删除角色"""
        result = messagebox.askyesno(
            "确认删除",
            f"确定要删除角色 '{role.name}' 吗？\n此操作不可撤销。"
        )

        if result:
            try:
                success = self.app_controller.role_controller.delete_role(role.id)
                if success:
                    # 从本地列表中移除
                    self.roles.remove(role)
                    # 刷新显示
                    self.refresh_cards()
                    messagebox.showinfo("成功", f"角色 '{role.name}' 已删除")
                else:
                    messagebox.showerror("错误", "删除角色失败")
            except Exception as e:
                messagebox.showerror("错误", f"删除角色失败: {str(e)}")

    def on_search(self, event):
        """搜索角色"""
        self.refresh_cards()

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
        from app.ui.voice_library_frame import VoiceLibraryFrame

        # 创建音色库窗口
        voice_window = tk.Toplevel(self.parent)
        voice_window.title("音色库管理")
        voice_window.geometry("1000x700")
        voice_window.transient(self.parent)
        voice_window.grab_set()

        # 创建音色库界面
        voice_library = VoiceLibraryFrame(voice_window, self.current_project, self.app_controller)
        voice_library.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 居中显示
        voice_window.update_idletasks()
        x = (voice_window.winfo_screenwidth() - voice_window.winfo_width()) // 2
        y = (voice_window.winfo_screenheight() - voice_window.winfo_height()) // 2
        voice_window.geometry(f"+{x}+{y}")
