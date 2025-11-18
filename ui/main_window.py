# ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from app.core.app_context import AppContext
from app.controllers.base_controller import BusinessException
from app.ui.chapter_editor import ChapterEditor


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("清影配音软件 v1.0")
        self.root.geometry("1200x800")

        self.app_controller = AppContext.get_instance()
        self.current_project = None  # 添加当前项目状态
        self.current_main_module = None  # 当前主模块：'dubbing' 或 'settings'

        self.setup_ui()
        self.load_projects()
        self.is_debug = True

    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建顶部主功能区
        self.create_main_toolbar(main_frame)

        # 创建主内容区域
        self.create_main_content(main_frame)

        # 创建底部状态栏
        self.create_status_bar(main_frame)

    def create_main_toolbar(self, parent):
        """创建顶部主功能区"""
        toolbar_frame = ttk.LabelFrame(parent, text="主功能区", padding="10")
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        # 主功能按钮
        main_functions = [
            ("🎤 配音模块", "dubbing", self.show_dubbing_module),
            ("⚙️ 设置模块", "settings", self.show_settings_module),
        ]

        for i, (text, module_id, command) in enumerate(main_functions):
            btn = ttk.Button(toolbar_frame, text=text, command=command, width=15)
            btn.pack(side=tk.LEFT, padx=5)

        # 项目操作按钮
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        ttk.Button(toolbar_frame, text="新建项目", command=self.new_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="打开项目", command=self.open_project).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar_frame, text="保存项目", command=self.save_project).pack(side=tk.LEFT, padx=2)

        # 项目信息显示在右侧
        info_frame = ttk.Frame(toolbar_frame)
        info_frame.pack(side=tk.RIGHT, padx=10)

        self.project_name_var = tk.StringVar(value="无项目")
        ttk.Label(info_frame, text="项目:", font=("Arial", 9)).pack(side=tk.LEFT)
        ttk.Label(info_frame, textvariable=self.project_name_var,
                  foreground="blue", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(2, 10))

        self.chapter_count_var = tk.StringVar(value="章节:0")
        ttk.Label(info_frame, textvariable=self.chapter_count_var, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

        self.character_count_var = tk.StringVar(value="角色:0")
        ttk.Label(info_frame, textvariable=self.character_count_var, font=("Arial", 9)).pack(side=tk.LEFT, padx=5)

    def create_main_content(self, parent):
        """创建主内容区域"""
        content_frame = ttk.Frame(parent)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 初始显示欢迎页面
        self.welcome_frame = ttk.Frame(content_frame)
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)

        self.show_welcome_page()

        # 模块容器（初始隐藏）
        self.module_container = ttk.Frame(content_frame)

    def show_welcome_page(self):
        """显示欢迎页面"""
        # 清空欢迎页面
        for widget in self.welcome_frame.winfo_children():
            widget.destroy()

        # 标题
        title_label = ttk.Label(
            self.welcome_frame,
            text="🎵 音频制作工具",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=(50, 10))

        subtitle_label = ttk.Label(
            self.welcome_frame,
            text="专业音频制作与角色推理平台",
            font=("Arial", 14)
        )
        subtitle_label.pack(pady=(0, 30))

        # 操作按钮
        button_frame = ttk.Frame(self.welcome_frame)
        button_frame.pack(pady=20)

        # ttk.Button(
        #     button_frame,
        #     text="新建项目",
        #     command=self.new_project,
        #     width=20
        # ).pack(pady=5)
        #
        # ttk.Button(
        #     button_frame,
        #     text="打开项目",
        #     command=self.open_project,
        #     width=20
        # ).pack(pady=5)

        # 使用说明
        help_frame = ttk.LabelFrame(self.welcome_frame, text="使用说明", padding="20")
        help_frame.pack(pady=30, padx=100, fill=tk.X)

        help_text = """1. 新建项目：创建一个新的配音项目
2. 打开项目：打开已有的配音项目
3. 配音模块：管理章节、角色和台词
4. 设置模块：配置项目参数和音频设置"""

        help_label = ttk.Label(help_frame, text=help_text, justify=tk.LEFT)
        help_label.pack()

    def create_module_tabs(self, module_type):
        """创建模块标签页"""
        # 隐藏欢迎页面，显示模块容器
        self.welcome_frame.pack_forget()
        self.module_container.pack(fill=tk.BOTH, expand=True)

        # 清除现有的标签页
        for widget in self.module_container.winfo_children():
            widget.destroy()

        if module_type == "dubbing":
            # 配音模块的标签页
            self.create_dubbing_tabs()
        elif module_type == "settings":
            # 设置模块的标签页
            self.create_settings_tabs()

    def create_dubbing_tabs(self):
        """创建配音模块的标签页"""
        # 标签页控件
        self.dubbing_notebook = ttk.Notebook(self.module_container)
        self.dubbing_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建各个配音功能标签页（先创建空框架）
        self.chapter_frame = ttk.Frame(self.dubbing_notebook)
        self.role_frame = ttk.Frame(self.dubbing_notebook)
        self.audio_frame = ttk.Frame(self.dubbing_notebook)

        self.dubbing_notebook.add(self.chapter_frame, text="📝 章节编辑")
        self.dubbing_notebook.add(self.role_frame, text="🎭 角色库")
        self.dubbing_notebook.add(self.audio_frame, text="🎵 音频生成")

        # 绑定标签页切换事件
        self.dubbing_notebook.bind("<<NotebookTabChanged>>", self.on_dubbing_tab_changed)

    def on_dubbing_tab_changed(self, event):
        """配音模块标签页切换事件"""
        if not self.current_project:
            return

        current_tab = self.dubbing_notebook.index(self.dubbing_notebook.select())

        if current_tab == 0:  # 章节编辑标签页
            self.setup_chapter_editor()
        elif current_tab == 1:  # 角色推理标签页
            self.setup_role_library()
        elif current_tab == 2:  # 音频生成标签页
            self.setup_audio_generation()

    def setup_chapter_editor(self):
        """设置章节编辑器（延迟加载）"""
        if self.is_debug:
            print("setup_chapter_editor called")  # 调试用
        # 清除现有内容
        for widget in self.chapter_frame.winfo_children():
            widget.destroy()

        if not self.current_project:
            # 如果没有项目，显示提示
            ttk.Label(
                self.chapter_frame,
                text="请先创建或打开一个项目",
                font=("Arial", 12)
            ).pack(expand=True, pady=50)
            return

        # 创建章节管理界面
        self.chapter_editor = ChapterEditor(self.chapter_frame, self.current_project, self.app_controller)
        self.chapter_editor.pack(fill=tk.BOTH, expand=True)
        self.chapter_editor_created = True

    def setup_role_library(self):
        """设置角色库界面（延迟加载）"""  # 修改方法名和注释
        # 清除现有内容
        for widget in self.role_frame.winfo_children():
            widget.destroy()

        if not self.current_project:
            ttk.Label(
                self.role_frame,
                text="请先创建或打开一个项目",
                font=("Arial", 12)
            ).pack(expand=True, pady=50)
            return

        # 创建角色库界面
        from app.ui.role_editor import RoleEditor
        self.role_editor = RoleEditor(self.role_frame, self.current_project, self.app_controller)
        self.role_editor.pack(fill=tk.BOTH, expand=True)

    def setup_audio_generation(self):
        """设置音频生成界面（延迟加载）"""
        # 清除现有内容
        for widget in self.audio_frame.winfo_children():
            widget.destroy()

        if not self.current_project:
            ttk.Label(
                self.audio_frame,
                text="请先创建或打开一个项目",
                font=("Arial", 12)
            ).pack(expand=True, pady=50)
            return

        # 这里可以添加音频生成界面的初始化代码
        ttk.Label(
            self.audio_frame,
            text="音频生成功能开发中...",
            font=("Arial", 12)
        ).pack(expand=True, pady=50)

    def create_settings_tabs(self):
        """创建设置模块的标签页"""
        # 标签页控件
        self.settings_notebook = ttk.Notebook(self.module_container)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 项目设置标签页
        self.project_settings_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(self.project_settings_frame, text="⚙️ 项目设置")

        # LLM配置标签页
        self.llm_settings_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(self.llm_settings_frame, text="🤖 LLM配置")

        # 项目设置内容
        # self.setup_project_settings()

        # LLM配置内容
        self.setup_llm_settings()


    def setup_project_settings(self):
        """设置项目设置页面内容"""
        # 清除现有内容
        for widget in self.project_settings_frame.winfo_children():
            widget.destroy()

        # 项目设置内容
        ttk.Label(self.project_settings_frame, text="项目设置",
                  font=("Arial", 16, "bold")).pack(anchor=tk.W, pady=(0, 20))

        # 项目基本信息
        info_frame = ttk.LabelFrame(self.project_settings_frame, text="项目信息", padding="10")
        info_frame.pack(fill=tk.X, pady=10)

        if self.current_project:
            info = self.current_project.get_project_info()
            ttk.Label(info_frame, text=f"项目名称: {info['name']}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"文件路径: {info['path']}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"创建时间: {info['created']}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"修改时间: {info['modified']}").pack(anchor=tk.W)

        # 音频设置
        audio_frame = ttk.LabelFrame(self.project_settings_frame, text="音频设置", padding="10")
        audio_frame.pack(fill=tk.X, pady=10)

        ttk.Label(audio_frame, text="默认输出格式:").pack(anchor=tk.W)
        format_combo = ttk.Combobox(audio_frame, values=["MP3", "WAV", "FLAC"], state="readonly")
        format_combo.set("MP3")
        format_combo.pack(anchor=tk.W, pady=5)

        ttk.Label(audio_frame, text="默认采样率:").pack(anchor=tk.W)
        rate_combo = ttk.Combobox(audio_frame, values=["22050", "44100", "48000"], state="readonly")
        rate_combo.set("44100")
        rate_combo.pack(anchor=tk.W, pady=5)

    def setup_llm_settings(self):
        """设置LLM配置页面"""
        # 导入LLM设置界面
        from app.ui.llm_settings_frame import LLMSettingsFrame

        # 创建LLM设置界面
        self.llm_settings = LLMSettingsFrame(
            self.llm_settings_frame,
            self.current_project,
            self.app_controller
        )
        self.llm_settings.pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self, parent):
        """创建底部状态栏"""
        status_frame = ttk.Frame(parent, relief=tk.SUNKEN, padding="2")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(fill=tk.X)

    def show_dubbing_module(self):
        """显示配音模块"""
        self.current_main_module = 'dubbing'
        self.create_module_tabs('dubbing')

        # 默认显示第一个标签页（章节编辑）
        if hasattr(self, 'dubbing_notebook'):
            self.dubbing_notebook.select(0)
            self.on_dubbing_tab_changed(None)

    def show_settings_module(self):
        """显示设置模块"""
        self.current_main_module = 'settings'
        self.create_module_tabs('settings')

    def new_project(self):
        """新建项目"""
        try:
            from app.ui.project_window import ProjectDialog
            dialog = ProjectDialog(self.root, self.app_controller.project_controller)
            self.root.wait_window(dialog.dialog)
            if dialog.result:
                self.current_project = dialog.result
                self.update_project_info()
                # 自动打开配音模块
                self.show_dubbing_module()
                if self.is_debug:
                    print(self.current_project)
        except Exception as e:
            messagebox.showerror("错误", f"新建项目失败: {str(e)}")

    def open_project(self):
        """打开项目"""
        try:
            from app.ui.project_selection_dialog import ProjectSelectionDialog

            # 创建项目选择对话框
            dialog = ProjectSelectionDialog(self.root, self.app_controller.project_controller)
            self.root.wait_window(dialog.dialog)

            if dialog.selected_project:
                self.current_project = dialog.selected_project
                self.update_project_info()
                # 自动打开配音模块
                self.show_dubbing_module()


                # 如果有模块已经打开，刷新模块内容
                # if self.current_main_module:
                #     self.create_module_tabs(self.current_main_module)

            if self.is_debug:
                print(self.current_project)

        except Exception as e:
            messagebox.showerror("错误", f"打开项目失败: {str(e)}")

    def save_project(self):
        """保存项目"""
        try:
            # 这里实现保存项目的逻辑
            messagebox.showinfo("提示", "保存项目功能待实现")
        except Exception as e:
            messagebox.showerror("错误", f"保存项目失败: {str(e)}")

    def update_project_info(self):
        """更新项目信息显示"""
        if self.current_project:
            self.project_name_var.set(self.current_project.name)

            # 更新章节数和角色数
            try:
                chapter_count = self.app_controller.chapter_controller.get_chapter_count(self.current_project.id)
                # 获取角色数量 - 需要确保role_controller有get_role_count方法
                # 如果没有，可以使用 len(self.app_controller.role_controller.get_roles_by_project(self.current_project.id))
                roles = self.app_controller.role_controller.get_roles_by_project(self.current_project.id)
                role_count = len(roles)

                self.chapter_count_var.set(f"章节:{chapter_count}")
                self.character_count_var.set(f"角色:{role_count}")
            except:
                self.chapter_count_var.set("章节:0")
                self.character_count_var.set("角色:0")

            # 如果当前在配音模块的角色库标签页，刷新内容
            if (self.current_main_module == 'dubbing' and
                    hasattr(self, 'dubbing_notebook') and
                    self.dubbing_notebook.index(self.dubbing_notebook.select()) == 1):  # 角色库标签页

                # 强制重新创建角色库界面
                if hasattr(self, 'role_editor'):
                    delattr(self, 'role_editor')
                self.setup_role_library()

    def load_projects(self):
        """加载项目列表"""
        try:
            projects = self.app_controller.project_controller.get_all_projects()
            # 更新项目列表显示
        except BusinessException as e:
            messagebox.showerror("错误", e.message)
        except Exception as e:
            messagebox.showerror("错误", f"加载项目失败: {str(e)}")
