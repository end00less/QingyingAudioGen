# ui/modern_main_window.py
import flet as ft
from flet import (
    Colors, Icons, padding, alignment, border_radius,
    TextStyle, FontWeight, MainAxisAlignment, CrossAxisAlignment, Container
)
import os
from typing import Optional, List, Dict, Any

# 导入配音工作台
from app.ui.modern_dubbing_workstation import ModernDubbingWorkstation


class ModernMainWindow:
    def __init__(self, page: ft.Page, app_controller=None):
        self.page = page
        self.app_controller = app_controller
        self.current_project = None
        self.current_view = "home"  # 改为首页
        self.nav_buttons = {}
        self.sidebar_visible = True  # 侧边栏默认可见

        # 初始化页面
        self.setup_page()
        self.create_main_layout()

    def setup_page(self):
        """设置页面配置"""
        self.page.title = "清影配音软件 v2.0"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window.width = 1400
        self.page.window.height = 900
        self.page.window.min_width = 1200
        self.page.window.min_height = 800

    def create_main_layout(self):
        """创建主布局"""
        # 创建侧边栏和内容区域容器
        self.sidebar_container = self.create_sidebar()
        self.content_container = self.create_content_area()

        # 主布局使用Row，包含侧边栏和内容区域
        self.main_row = ft.Row([
            self.sidebar_container,
            self.content_container,
        ], expand=True)

        main_content = ft.Container(
            content=self.main_row,
            padding=10,
            expand=True
        )

        self.page.add(main_content)

    def create_sidebar(self):
        self.sidebar_content = ft.Column([
            # Logo区域
            self.create_logo_section(),

            # 导航菜单
            self.create_navigation_menu(),

            # 底部操作区
            self.create_bottom_actions(),
        ], expand=True)

        return ft.Container(
            content=self.sidebar_content,
            width=280,
            bgcolor=Colors.BLUE_GREY_50,
            border_radius=10,
            margin=padding.only(right=10)
        )

    def create_logo_section(self):
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "🎵 清影配音",
                    size=24,
                    weight=FontWeight.BOLD,
                    color=Colors.BLUE_GREY_900,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Divider(color=Colors.BLUE_GREY_300, height=20)
            ]),
            padding=20,
            height=100
        )

    def create_navigation_menu(self):
        nav_items = [
            ("🏠 首页", "home", self.show_home),
            ("🎤 开始配音", "dubbing", self.show_dubbing),
            ("🎵 音色管理", "voice_management", self.show_voice_management),
            ("🎭 角色设置", "role_settings", self.show_role_settings),
            ("🤖 克隆必要配置", "clone_config", self.show_clone_config),
            ("💬 提示词设置", "prompt_settings", self.show_prompt_settings),
        ]

        nav_controls = []
        for text, key, command in nav_items:
            btn = ft.ElevatedButton(
                text=text,
                on_click=command,
                style=ft.ButtonStyle(
                    color=Colors.BLUE_GREY_800,
                    bgcolor=Colors.TRANSPARENT,
                    shadow_color=Colors.TRANSPARENT,
                    overlay_color=ft.Colors.with_opacity(0.1, Colors.BLUE_GREY_300),
                    padding=padding.symmetric(15, 20),
                    alignment=alignment.center_left,
                ),
                expand=True,
            )
            self.nav_buttons[key] = btn
            nav_controls.append(btn)

        return ft.Container(
            content=ft.Column(nav_controls, spacing=2),
            padding=padding.symmetric(10, 0),
            expand=True
        )

    def create_bottom_actions(self):
        return ft.Container(
            content=ft.ElevatedButton(
                text="➕ 新建项目",
                icon=Icons.ADD,
                on_click=self.new_project,
                style=ft.ButtonStyle(
                    bgcolor=Colors.GREEN_600,
                    color=Colors.WHITE,
                    padding=padding.symmetric(20, 15),
                ),
                expand=True,
            ),
            padding=20
        )

    def create_content_area(self):
        self.content_display = ft.Container(
            content=self.show_home_view(),  # 默认显示首页
            expand=True,
            bgcolor=Colors.WHITE,
            border_radius=10,
            padding=15
        )
        return self.content_display

    def toggle_sidebar(self, visible: bool):
        """切换侧边栏显示/隐藏"""
        self.sidebar_visible = visible
        if visible:
            self.sidebar_container.visible = True
            self.sidebar_container.width = 280
        else:
            self.sidebar_container.visible = False
            self.sidebar_container.width = 0

        self.page.update()

    def show_home(self, e=None):
        """显示首页"""
        self.current_view = "home"
        self.update_nav_button("home")
        self.toggle_sidebar(True)  # 显示侧边栏
        self.content_display.content = self.show_home_view()
        self.page.update()

    def show_home_view(self):
        """首页视图"""
        return ft.Column([
            self.create_page_header("🏠 首页", "欢迎使用清影配音软件"),
            self.create_projects_grid()
        ], expand=True)

    def show_dubbing(self, e=None):
        """显示配音工作台"""
        self.current_view = "dubbing"
        self.update_nav_button("dubbing")

        if self.current_project:
            # 隐藏侧边栏
            self.toggle_sidebar(False)

            # 创建配音工作台（全屏版本）
            dubbing_workstation = ModernDubbingWorkstation(
                self.page,
                self.app_controller,
                self.current_project,
                on_back_callback=self.show_home  # 返回时显示首页和侧边栏
            )

            # 直接设置内容区域为配音工作台
            self.content_display.content = dubbing_workstation
        else:
            # 没有选择项目时显示提示
            self.content_display.content = self.create_no_project_view()

        self.page.update()

    # 其他方法保持不变...
    def show_voice_management(self, e=None):
        """显示音色管理"""
        self.current_view = "voice_management"
        self.update_nav_button("voice_management")
        self.toggle_sidebar(True)  # 显示侧边栏
        self.content_display.content = self.show_voice_management_view()
        self.page.update()

    def show_voice_management_view(self):
        """音色管理视图"""
        return ft.Column([
            self.create_page_header("🎵 音色管理", "管理和配置音色库"),
            ft.Container(
                content=ft.Column([
                    ft.Text("音色管理功能开发中...", size=18, color=Colors.BLUE_GREY_900),
                    ft.Text("这里可以管理TTS音色、克隆音色等", color=Colors.GREY_600)
                ], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER),
                expand=True
            )
        ], expand=True)

    def show_role_settings(self, e=None):
        """显示角色设置"""
        self.current_view = "role_settings"
        self.update_nav_button("role_settings")
        self.toggle_sidebar(True)  # 显示侧边栏
        self.content_display.content = self.show_role_settings_view()
        self.page.update()

    def show_role_settings_view(self):
        """角色设置视图"""
        return ft.Column([
            self.create_page_header("🎭 角色设置", "配置角色参数和属性"),
            ft.Container(
                content=ft.Column([
                    ft.Text("角色设置功能开发中...", size=18, color=Colors.BLUE_GREY_900),
                    ft.Text("配置角色的声音、情绪等参数", color=Colors.GREY_600)
                ], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER),
                expand=True
            )
        ], expand=True)

    def show_clone_config(self, e=None):
        """显示克隆必要配置"""
        self.current_view = "clone_config"
        self.update_nav_button("clone_config")
        self.toggle_sidebar(True)  # 显示侧边栏
        self.content_display.content = self.show_clone_config_view()
        self.page.update()

    def show_clone_config_view(self):
        """克隆配置视图"""
        return ft.Column([
            self.create_page_header("🤖 克隆必要配置", "配置声音克隆相关参数"),
            ft.Container(
                content=ft.Column([
                    ft.Text("克隆配置功能开发中...", size=18, color=Colors.BLUE_GREY_900),
                    ft.Text("配置声音克隆的模型参数和训练设置", color=Colors.GREY_600)
                ], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER),
                expand=True
            )
        ], expand=True)

    def show_prompt_settings(self, e=None):
        """显示提示词设置"""
        self.current_view = "prompt_settings"
        self.update_nav_button("prompt_settings")
        self.toggle_sidebar(True)  # 显示侧边栏
        self.content_display.content = self.show_prompt_settings_view()
        self.page.update()

    def show_prompt_settings_view(self):
        """提示词设置视图"""
        return ft.Column([
            self.create_page_header("💬 提示词设置", "管理和配置提示词模板"),
            ft.Container(
                content=ft.Column([
                    ft.Text("提示词设置功能开发中...", size=18, color=Colors.BLUE_GREY_900),
                    ft.Text("管理LLM提示词、角色对话模板等", color=Colors.GREY_600)
                ], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER),
                expand=True
            )
        ], expand=True)

    def create_page_header(self, title, subtitle=""):
        self.search_field = ft.TextField(
            label="搜索项目...",
            width=300,
            on_change=self.on_search_projects,
            suffix_icon=Icons.SEARCH
        )

        header_content = [
            ft.Column([
                ft.Text(title, size=24, weight=FontWeight.BOLD, color=Colors.BLUE_GREY_900),
                ft.Text(subtitle, color=Colors.GREY_600) if subtitle else None
            ], expand=True)
        ]

        if title == "🏠 首页":  # 只在首页显示搜索框
            header_content.append(self.search_field)

        return ft.Container(
            content=ft.Row(
                header_content,
                alignment=MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=padding.only(bottom=20)
        )

    def create_projects_grid(self):
        self.projects_grid = ft.GridView(
            controls=self.load_project_cards(),
            expand=True,
            runs_count=3,
            max_extent=300,
            spacing=10,
            run_spacing=10,
        )
        return self.projects_grid

    def load_project_cards(self):
        projects = self.get_projects_data()
        cards = []

        for i, project in enumerate(projects):
            cards.append(self.create_project_card(project, i))

        return cards

    def get_projects_data(self):
        if self.app_controller:
            try:
                projects = self.app_controller.project_controller.get_all_projects()
                return projects
            except Exception as e:
                print(f"获取项目数据失败: {e}")

        # 返回示例数据
        return [
            {"name": "科幻小说配音", "chapters": 12, "roles": 8, "last_modified": "2024-01-15"},
            {"name": "儿童故事集", "chapters": 24, "roles": 15, "last_modified": "2024-01-14"},
            {"name": "历史纪录片", "chapters": 8, "roles": 6, "last_modified": "2024-01-13"},
            {"name": "商业广告", "chapters": 3, "roles": 4, "last_modified": "2024-01-12"},
        ]

    def create_project_card(self, project, index):
        if isinstance(project, dict):
            project_name = project.get("name", "未命名项目")
            chapters = project.get("chapters", 0)
            roles = project.get("roles", 0)
            last_modified = project.get("last_modified", "未知时间")
        else:
            try:
                project_name = project.name
                chapters = 0
                roles = 0

                if self.app_controller and project.id:
                    try:
                        chapters_list = self.app_controller.chapter_controller.get_chapters_by_project(project.id)
                        chapters = len(chapters_list) if chapters_list else 0
                    except:
                        chapters = 0

                    try:
                        roles_list = self.app_controller.role_controller.get_roles_by_project(project.id)
                        roles = len(roles_list) if roles_list else 0
                    except:
                        roles = 0

                if project.updated_at:
                    last_modified = project.updated_at.strftime('%Y-%m-%d')
                elif project.created_at:
                    last_modified = project.created_at.strftime('%Y-%m-%d')
                else:
                    last_modified = "未知时间"

            except Exception as e:
                print(f"处理项目对象时出错: {e}")
                project_name = "项目加载失败"
                chapters = 0
                roles = 0
                last_modified = "未知时间"

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("📁", size=24),
                        ft.Text(
                            project_name,
                            size=16,
                            weight=FontWeight.BOLD,
                            color=Colors.BLUE_GREY_900,
                            expand=True,
                            max_lines=2,
                            overflow=ft.TextOverflow.ELLIPSIS
                        )
                    ]),
                    ft.Container(
                        content=ft.Text(
                            f"📝 {chapters} 章节  🎭 {roles} 角色",
                            color=Colors.GREY_700
                        ),
                        padding=padding.only(top=10, bottom=5)
                    ),
                    ft.Text(
                        f"最后修改: {last_modified}",
                        size=12,
                        color=Colors.GREY_600
                    ),
                    ft.Row([
                        ft.TextButton(
                            text="打开",
                            icon=Icons.OPEN_IN_NEW,
                            on_click=lambda e, p=project: self.open_project_card(p),
                            style=ft.ButtonStyle(
                                color=Colors.BLUE_600
                            )
                        ),
                        ft.TextButton(
                            text="删除",
                            icon=Icons.DELETE,
                            on_click=lambda e, p=project: self.delete_project_card(p),
                            style=ft.ButtonStyle(
                                color=Colors.RED_600
                            )
                        ),
                    ], alignment=MainAxisAlignment.SPACE_BETWEEN)
                ]),
                padding=20,
                width=280,
                height=180
            ),
            elevation=5,
            margin=5
        )

    def create_no_project_view(self):
        return ft.Container(
            content=ft.Column([
                ft.Icon(Icons.WARNING_AMBER, size=64, color=Colors.ORANGE),
                ft.Text(
                    "请先从首页中选择一个项目",
                    size=18,
                    color=Colors.GREY_600
                ),
                ft.ElevatedButton(
                    text="返回首页",
                    icon=Icons.ARROW_BACK,
                    on_click=self.show_home,
                    style=ft.ButtonStyle(
                        bgcolor=Colors.BLUE_600,
                        color=Colors.WHITE
                    )
                )
            ], alignment=MainAxisAlignment.CENTER, horizontal_alignment=CrossAxisAlignment.CENTER),
            alignment=alignment.center,
            expand=True
        )

    def open_project_card(self, project):
        self.current_project = project
        self.show_dubbing()

    def delete_project_card(self, project):
        project_name = getattr(project, 'name', '未知项目')
        project_id = getattr(project, 'id', None)

        def confirm_delete(e):
            if project_id and self.app_controller:
                try:
                    success = self.app_controller.project_controller.delete_project(project_id)
                    if success:
                        self.show_snack_bar("项目删除成功")
                        self.show_home()
                    else:
                        self.show_snack_bar("项目删除失败")
                except Exception as e:
                    self.show_snack_bar(f"删除项目时发生错误: {str(e)}")
            self.page.dialog.open = False
            self.page.update()

        def cancel_delete(e):
            self.page.dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("确认删除"),
            content=ft.Text(f"确定要删除项目 '{project_name}' 吗？\n此操作不可撤销！"),
            actions=[
                ft.TextButton("取消", on_click=cancel_delete),
                ft.TextButton("删除", on_click=confirm_delete, style=ft.ButtonStyle(color=Colors.RED)),
            ],
            actions_alignment=MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def new_project(self, e):
        if self.app_controller:
            from app.ui.project_dialog import ProjectDialog
            self.show_snack_bar("新建项目功能")

    def update_nav_button(self, active_key):
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.style.bgcolor = Colors.BLUE_600
                btn.style.color = Colors.WHITE
            else:
                btn.style.bgcolor = Colors.TRANSPARENT
                btn.style.color = Colors.BLUE_GREY_800
        self.page.update()

    def on_search_projects(self, e):
        search_text = e.control.value.lower()
        print(f"搜索: {search_text}")

    def show_snack_bar(self, message):
        snack_bar = ft.SnackBar(content=ft.Text(message))
        self.page.overlay.append(snack_bar)
        snack_bar.open = True
        self.page.update()