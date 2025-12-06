import flet as ft
import flet.canvas as cv
import os
import threading
import time
import subprocess
import tempfile
import shutil
import numpy as np
from typing import Optional, List, Dict, Any, Callable, Tuple
from app.services.audio_player_service import audio_player
# 在文件顶部导入
from app.core.audio_engine import AudioProcessor




class ModernDubbingWorkstation(ft.Container):
    def __init__(self, page, app_controller, project, on_back_callback=None):
        super().__init__()
        self.page = page
        self.app_controller = app_controller
        self.project = project
        self.chapter_controller = app_controller.chapter_controller
        self.line_controller = app_controller.line_controller
        self.role_controller = app_controller.role_controller
        self.on_back_callback = on_back_callback

        self.current_chapter_id = None
        self.current_line_id = None
        self.current_chapter = None

        self.chapter_cards = []
        self.line_rows = []
        self.roles_data = []  # 存储角色数据

        # 音频轨道相关属性
        self.waveform_data = None
        self.audio_duration = 0
        self.selection_start = None
        self.selection_end = None
        self.is_selecting = False
        self.mouse_down_pos = None
        self.last_click_time = 0

        # 初始化容器属性
        self.padding = 10  # 减少padding
        self.expand = True
        self.bgcolor = ft.Colors.WHITE

        # 创建UI内容
        self.content = self.create_main_layout()

        # 初始化后立即加载章节数据
        self.load_chapters()
        self.load_roles()  # 加载角色列表

    def create_main_layout(self):
        return ft.Column([
            self.create_header(),
            self.create_main_content(),
        ], spacing=5)  # 减少间距

    def create_header(self):
        # 显示项目名称
        project_name = getattr(self.project, 'name', '未知项目')
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        "🎤 配音工作台",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_GREY_900
                    ),
                    ft.Text(
                        f"项目: {project_name}",
                        size=14,
                        color=ft.Colors.GREY_600
                    )
                ]),
                ft.Row([
                    ft.ElevatedButton(
                        text="⚙️ 项目设置",
                        icon=ft.Icons.SETTINGS,
                        on_click=self.open_project_settings,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.GREEN_600,
                            padding=ft.padding.symmetric(15, 10)  # 减少padding
                        )
                    ),
                    ft.ElevatedButton(
                        text="🔙 返回首页",
                        icon=ft.Icons.ARROW_BACK,
                        on_click=self.go_back,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.RED_600,
                            padding=ft.padding.symmetric(15, 10)  # 减少padding
                        )
                    ),
                ], alignment=ft.MainAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(15, 5),  # 减少padding
            margin=ft.padding.only(bottom=10)  # 减少margin
        )

    def create_main_content(self):
        return ft.Row([
            # 左侧章节列表（缩小宽度）
            ft.Container(
                content=self.create_chapter_list(),
                width=220,  # 进一步缩小
                margin=ft.padding.all(3),  # 减少margin
                bgcolor=ft.Colors.BLUE_GREY_50,
                border_radius=8,
                padding=5  # 减少padding
            ),
            # 右侧内容区域
            ft.Container(
                content=self.create_content_area(),
                expand=True,
                margin=ft.padding.all(3),  # 减少margin
                bgcolor=ft.Colors.BLUE_GREY_50,
                border_radius=8,
                padding=5  # 减少padding
            ),
        ], expand=True, spacing=5)  # 减少间距

    def create_chapter_list(self):
        self.chapter_listview = ft.ListView(
            controls=[],
            expand=True,
            spacing=2  # 减少间距
        )

        return ft.Column([
            # 标题栏
            ft.Container(
                content=ft.Row([
                    ft.Text(
                        "📚 章节列表",
                        size=16,  # 减小字体
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_GREY_900
                    ),
                    ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            tooltip="添加章节",
                            on_click=self.add_chapter,
                            icon_color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.GREEN_600
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH,
                            tooltip="刷新列表",
                            on_click=lambda e: self.load_chapters(),
                            icon_color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.BLUE_600
                        ),
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=5  # 减少padding
            ),
            # 章节列表
            ft.Container(
                content=self.chapter_listview,
                expand=True
            )
        ], spacing=2)  # 减少间距

    def create_content_area(self):
        return ft.Column([
            # 章节内容区域（大幅缩小）
            ft.Container(
                content=self.create_chapter_content(),
                height=80,  # 大幅减小高度
                margin=ft.padding.only(bottom=5),  # 减少margin
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                padding=5  # 减少padding
            ),
            # 台词管理区域（占据主要空间）
            ft.Container(
                content=self.create_lines_management(),
                expand=True,
                bgcolor=ft.Colors.WHITE,
                border_radius=8,
                padding=5  # 减少padding
            ),
        ], expand=True, spacing=5)  # 减少间距

    def create_chapter_content(self):
        self.chapter_status_text = ft.Text(
            "请选择章节",
            color=ft.Colors.GREY_600,
            size=12  # 减小字体
        )

        self.chapter_content_field = ft.TextField(
            multiline=True,
            min_lines=2,  # 减少行数
            max_lines=2,
            border=ft.InputBorder.NONE,
            text_style=ft.TextStyle(size=12),  # 减小字体
            read_only=True
        )

        return ft.Column([
            ft.Row([
                ft.Text(
                    "📝 章节内容",
                    size=14,  # 减小字体
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_GREY_900
                ),
                ft.Row([
                    self.chapter_status_text,
                    ft.ElevatedButton(
                        text="📄 导入",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=self.import_text_with_parsing,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.PURPLE_600,
                            color=ft.Colors.WHITE,
                            padding=ft.padding.symmetric(10, 5)  # 减少padding
                        )
                    ),
                ], alignment=ft.MainAxisAlignment.END),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

            ft.Container(
                content=self.chapter_content_field,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=5,
                padding=5  # 减少padding
            )
        ], spacing=2)  # 减少间距

    def create_lines_management(self):
        """台词管理区域"""
        return ft.Column([
            # 标题栏
            ft.Container(
                content=ft.Row([
                    ft.Text(
                        "🎭 台词管理",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_GREY_900
                    ),
                    ft.Row([
                        ft.ElevatedButton(
                            text="➕ 添加",
                            on_click=self.add_new_line,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.GREEN_600,
                                color=ft.Colors.WHITE,
                                padding=ft.padding.symmetric(10, 5)  # 减少padding
                            )
                        ),
                        ft.ElevatedButton(
                            text="🎵 批量生成",
                            on_click=self.batch_generate_audio,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.BLUE_600,
                                color=ft.Colors.WHITE,
                                padding=ft.padding.symmetric(10, 5)  # 减少padding
                            )
                        ),
                        self.create_export_menu(),
                    ]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=5  # 减少padding
            ),
            # 可编辑的台词表格
            self.create_editable_lines_table(),
        ], expand=True, spacing=5)  # 减少间距

    def create_editable_lines_table(self):
        """创建可编辑的台词表格"""
        # 表头 - 调整各列宽度
        headers = [
            ("序号", 50),  # 稍微增加宽度
            ("台词内容", 450),  # 大幅增加宽度
            ("角色", 110),  # 稍微缩短，从150改为130
            ("情绪", 110),  # 稍微缩短，从150改为130
            ("强度", 110),  # 稍微缩短，从150改为130
            ("试听设置", 380),  # 增加试听设置列宽度
            ("状态", 80),  # 稍微增加状态列宽度
            ("操作", 180)  # 增加操作列宽度
        ]

        header_row = ft.Row([
            ft.Container(
                content=ft.Text(
                    header_text,
                    size=11,  # 减小字体
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_GREY_900,
                    text_align=ft.TextAlign.CENTER
                ),
                width=width,
                padding=3  # 减少padding
            ) for header_text, width in headers
        ])

        # 可编辑的台词列表
        self.editable_lines_list = ft.Column([], scroll=ft.ScrollMode.AUTO, spacing=1)

        return ft.Column([
            # 表格
            ft.Column([
                header_row,
                ft.Container(
                    content=ft.Column([
                        self.editable_lines_list
                    ], scroll=ft.ScrollMode.AUTO),
                    border=ft.border.all(1, ft.Colors.GREY_400),
                    border_radius=5,
                    height=620  # 增加表格高度
                )
            ], expand=True)
        ], expand=True)

    def create_editable_line_row(self, line, index):
        """创建可编辑的台词行"""
        # 获取台词数据
        line_text = getattr(line, 'text_content', '') or getattr(line, 'text', '')
        role_id = getattr(line, 'role_id', None)
        emotion_id = getattr(line, 'emotion_id', None)
        strength_id = getattr(line, 'strength_id', None)
        status = getattr(line, 'status', 'pending')

        # 获取音频文件的当前设置（从数据库读取）
        saved_speed = getattr(line, 'speed', 1.0)  # 默认1.0x
        saved_volume = getattr(line, 'volume', 100.0)  # 默认100%

        # 检查音频文件是否存在
        audio_exists = False
        if hasattr(line, 'audio_path') and line.audio_path:
            audio_exists = os.path.exists(line.audio_path)

        # 获取角色名称
        role_name = self.get_role_name(role_id)
        emotion_name = self.get_emotion_name(emotion_id)
        strength_name = self.get_strength_name(strength_id)
        status_display = self.get_status_display(status)
        status_color = self.get_status_color(status)

        # 序号
        index_text = ft.Text(
            str(index),
            size=12,
            color=ft.Colors.BLUE_GREY_900,
            text_align=ft.TextAlign.CENTER
        )

        # 台词内容输入框
        text_field = ft.TextField(
            value=line_text,
            width=440,
            multiline=True,
            min_lines=1,
            max_lines=2,
            border=ft.InputBorder.NONE,
            text_style=ft.TextStyle(size=12),
            bgcolor=ft.Colors.TRANSPARENT
        )

        # 角色下拉框
        role_dropdown = ft.Dropdown(
            value=role_name,
            width=100,
            options=[ft.dropdown.Option(getattr(role, 'name', '未知')) for role in self.roles_data],
            text_style=ft.TextStyle(size=11),
            border=ft.InputBorder.OUTLINE,
            border_radius=5,
            content_padding=ft.padding.symmetric(10, 5)
        )

        # 情绪下拉框
        emotion_dropdown = ft.Dropdown(
            value=emotion_name,
            width=100,
            options=[
                ft.dropdown.Option("高兴"),
                ft.dropdown.Option("生气"),
                ft.dropdown.Option("伤心"),
                ft.dropdown.Option("害怕"),
                ft.dropdown.Option("厌恶"),
                ft.dropdown.Option("低落"),
                ft.dropdown.Option("惊喜"),
                ft.dropdown.Option("平静"),
            ],
            text_style=ft.TextStyle(size=11),
            border=ft.InputBorder.OUTLINE,
            border_radius=5,
            content_padding=ft.padding.symmetric(10, 5)
        )

        # 强度下拉框
        strength_dropdown = ft.Dropdown(
            value=strength_name,
            width=100,
            options=[
                ft.dropdown.Option("微弱"),
                ft.dropdown.Option("稍弱"),
                ft.dropdown.Option("中等"),
                ft.dropdown.Option("较强"),
                ft.dropdown.Option("强烈"),
            ],
            text_style=ft.TextStyle(size=11),
            border=ft.InputBorder.OUTLINE,
            border_radius=5,
            content_padding=ft.padding.symmetric(10, 5)
        )

        # 状态标签
        status_label = ft.Container(
            content=ft.Text(
                status_display,
                size=10,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD
            ),
            width=70,
            bgcolor=status_color,
            border_radius=12,
            alignment=ft.alignment.center,
        )

        # 速度显示和滑块
        speed_display = ft.Text(f"{saved_speed:.1f}x", size=10, color=ft.Colors.BLUE_GREY_700)

        def update_speed_display(speed_value):
            speed_display.value = f"{speed_value:.1f}x"
            self.page.update(speed_display)

        speed_slider = ft.Slider(
            min=0.5,
            max=2.0,
            divisions=15,
            value=saved_speed,
            width=120,
            on_change=lambda e: update_speed_display(float(e.control.value))
        )

        # 音量显示和滑块
        volume_display = ft.Text(f"{int(saved_volume)}%", size=10, color=ft.Colors.BLUE_GREY_700)

        def update_volume_display(volume_value):
            volume_display.value = f"{int(volume_value)}%"
            self.page.update(volume_display)

        volume_slider = ft.Slider(
            min=0,
            max=300,
            divisions=30,
            value=saved_volume,
            width=120,
            on_change=lambda e: update_volume_display(float(e.control.value))
        )

        # 试听按钮
        preview_btn = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            icon_size=16,
            tooltip="试听",
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_600 if audio_exists else ft.Colors.GREY_400,
            disabled=not audio_exists,
            on_click=lambda e: self.preview_audio_with_settings(line, speed_slider.value, volume_slider.value)
        )

        # 应用按钮
        def on_apply_click(e):
            self.apply_audio_processing(
                line,
                speed_slider.value,
                volume_slider.value,
                lambda: None  # 不需要重置回调
            )

        apply_btn = ft.IconButton(
            icon=ft.Icons.SETTINGS,
            icon_size=16,
            tooltip="应用",
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.TEAL_600 if audio_exists else ft.Colors.GREY_400,
            disabled=not audio_exists,
            on_click=on_apply_click
        )

        # 保存按钮
        save_btn = ft.IconButton(
            icon=ft.Icons.SAVE,
            icon_size=16,
            tooltip="保存",
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_600,
            on_click=lambda e: self.save_line_inline(line, text_field, role_dropdown, emotion_dropdown,
                                                     strength_dropdown)
        )

        # 生成音频按钮
        generate_btn = ft.IconButton(
            icon=ft.Icons.AUDIO_FILE,
            icon_size=16,
            tooltip="生成音频",
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.ORANGE_600,
            on_click=lambda e: self.generate_single_audio(line)
        )

        # 删除按钮
        delete_btn = ft.IconButton(
            icon=ft.Icons.DELETE,
            icon_size=16,
            tooltip="删除",
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_600,
            on_click=lambda e: self.delete_single_line(line)
        )

        # 音频轨道查看器 - 添加波形显示
        audio_track = self.create_audio_track_viewer(line, width=360, height=80)

        # 2. 然后获取 selection_time_text（现在应该已经存在了）
        if hasattr(line, '_audio_track_info'):
            selection_time_display = line._audio_track_info.get('selection_time_text')
        else:
            # 作为后备，创建一个临时的
            selection_time_display = ft.Text("未选择区域", size=8, color=ft.Colors.BLUE_700)

        # 3. 创建清除按钮
        cut_btn = ft.IconButton(
            icon=ft.Icons.CONTENT_CUT,
            icon_size=14,
            tooltip="剪切选中区间",
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_600,
            on_click=lambda e: self.cut_audio_segment(line)  # 调用新的剪切函数
        )

        # 4. 创建选中区间显示行
        selection_row = ft.Row([
            ft.Container(
                content=selection_time_display,
                expand=True,
                padding=ft.padding.only(left=5)
            ),
            cut_btn
        ], alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            height=28
        )

        # 试听设置区域 - 包含波形显示
        audio_settings = ft.Container(
            content=ft.Column([
                # 音频波形轨道
                audio_track,

                # 选中区间显示和清除按钮
                selection_row,



                # 速度控制
                ft.Row([
                    ft.Text("速度", size=10, color=ft.Colors.BLUE_GREY_700, width=30),
                    ft.Container(
                        content=speed_slider,
                        width=100
                    ),
                    speed_display
                ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                # 音量控制
                ft.Row([
                    ft.Text("音量", size=10, color=ft.Colors.BLUE_GREY_700, width=30),
                    ft.Container(
                        content=volume_slider,
                        width=100
                    ),
                    volume_display
                ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER),

                # 按钮控制
                ft.Row([
                    preview_btn,
                    apply_btn
                ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=5, tight=True),
            width=360,
            padding=ft.padding.symmetric(vertical=5, horizontal=10),
            bgcolor=ft.Colors.BLUE_GREY_50,
            border_radius=5
        )

        # 操作按钮区域
        action_buttons = ft.Row([
            save_btn,
            generate_btn,
            delete_btn
        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER)

        # 主行容器
        return ft.Container(
            content=ft.Column([
                # 第一行：基本信息
                ft.Row([
                    # 序号列
                    ft.Container(
                        content=index_text,
                        width=50,
                        alignment=ft.alignment.center,
                        padding=5
                    ),

                    # 台词内容列
                    ft.Container(
                        content=text_field,
                        width=450,
                        padding=5,
                        bgcolor=ft.Colors.BLUE_GREY_50 if index % 2 == 0 else ft.Colors.WHITE
                    ),

                    # 角色列
                    ft.Container(
                        content=role_dropdown,
                        width=110,
                        padding=5
                    ),

                    # 情绪列
                    ft.Container(
                        content=emotion_dropdown,
                        width=110,
                        padding=5
                    ),

                    # 强度列
                    ft.Container(
                        content=strength_dropdown,
                        width=110,
                        padding=5
                    ),

                    # 试听设置列
                    ft.Container(
                        content=audio_settings,
                        width=380,
                        padding=5
                    ),

                    # 状态列
                    ft.Container(
                        content=status_label,
                        width=80,
                        alignment=ft.alignment.center,
                        padding=5
                    ),

                    # 操作列
                    ft.Container(
                        content=action_buttons,
                        width=180,
                        alignment=ft.alignment.center,
                        padding=5
                    )
                ], spacing=0),

                # 第二行：音频轨道（仅在音频存在时显示）
                # ft.Container(
                #     content=audio_track,
                #     width=1290,  # 总宽度：50+450+110+110+110+380+80+180 = 1370，减去padding
                #     visible=audio_exists,  # 只有音频存在时才显示
                #     padding=ft.padding.only(left=40, right=5)  # 与上面行对齐
                # ) if audio_exists else ft.Container()  # 空容器
            ], spacing=0),
            bgcolor=ft.Colors.BLUE_GREY_50 if index % 2 == 0 else ft.Colors.WHITE,
            border=ft.border.only(bottom=ft.border.BorderSide(1, ft.Colors.GREY_300)),
            padding=ft.padding.symmetric(vertical=5)
        )

    def preview_audio_with_settings(self, line, speed, volume):
        """使用当前设置试听音频 - 使用行特定的进度指示器"""
        if not hasattr(line, 'audio_path') or not line.audio_path:
            self.show_snack_bar("音频文件不存在")
            return

        if not os.path.exists(line.audio_path):
            self.show_snack_bar("音频文件不存在，请先生成语音")
            return

        try:
            # 获取音频时长
            duration = self.get_audio_duration(line.audio_path)
            if duration <= 0:
                duration = 3.0

            # 获取这行音频的独立进度指示器
            if not hasattr(line, '_audio_track_info'):
                self.show_snack_bar("音频轨道未初始化")
                return

            audio_info = line._audio_track_info
            audio_info['total_duration'] = duration
            audio_info['playback_active'] = True

            # 显示试听提示
            self.show_snack_bar(f"正在试听: 速度{speed:.1f}x, 音量{volume}%...")

            # 重置并显示进度指示器
            if audio_info['progress_indicator']:
                audio_info['progress_indicator'].opacity = 1
                audio_info['progress_indicator'].left = 0
                audio_info['progress_indicator'].update()

            # 在后台线程中处理并播放音频
            def preview_in_background():
                try:
                    import time

                    # 准备参数
                    speed_value = float(speed)
                    volume_value = float(volume) / 100.0

                    # 创建临时预览文件
                    temp_dir = tempfile.gettempdir()
                    timestamp = int(time.time() * 1000)
                    preview_path = os.path.join(temp_dir, f"preview_{line.id}_{timestamp}.wav")

                    # 构建FFmpeg命令
                    ffmpeg_cmd = [
                        "ffmpeg", "-y", "-i", line.audio_path,
                        "-filter:a", f"atempo={speed_value},volume={volume_value}",
                        "-ac", "2", "-ar", "44100", "-acodec", "pcm_s16le",
                        preview_path
                    ]

                    print(f"预览FFmpeg命令: {' '.join(ffmpeg_cmd)}")

                    # 执行FFmpeg命令
                    ffmpeg_result = subprocess.run(
                        ffmpeg_cmd,
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore',
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )

                    if ffmpeg_result.returncode == 0 and os.path.exists(preview_path):
                        file_size = os.path.getsize(preview_path)
                        print(f"预览文件生成成功，大小: {file_size} 字节")

                        if file_size > 0:
                            # 计算实际播放时长
                            actual_duration = duration / speed_value if speed_value > 0 else duration

                            # 开始播放进度动画
                            self.start_playback_progress_animation_for_line(line, actual_duration)

                            # 播放音频
                            audio_player.stop_audio()
                            time.sleep(0.2)

                            # 使用音频播放器播放
                            if audio_player.play_audio(preview_path):
                                print(f"音频播放开始，时长: {actual_duration:.2f}秒")

                                # 等待播放完成（简单方式）
                                time.sleep(actual_duration + 0.5)  # 加0.5秒缓冲

                                # 播放完成
                                audio_info['playback_active'] = False
                                self.reset_playback_progress_for_line(line)

                                # 清理临时文件
                                self.cleanup_temp_file(preview_path)

                                def show_complete():
                                    self.show_snack_bar("试听完成")

                                self.page.add(ft.Container(width=0, height=0, on_click=lambda e: show_complete()))
                            else:
                                audio_info['playback_active'] = False
                                self.reset_playback_progress_for_line(line)
                                self.show_snack_bar("播放失败")
                        else:
                            audio_info['playback_active'] = False
                            self.reset_playback_progress_for_line(line)
                            self.show_snack_bar("预览文件生成失败")
                    else:
                        audio_info['playback_active'] = False
                        self.reset_playback_progress_for_line(line)
                        self.show_snack_bar("预览生成失败")

                except Exception as e:
                    print(f"试听处理失败: {e}")
                    import traceback
                    traceback.print_exc()
                    audio_info['playback_active'] = False
                    self.reset_playback_progress_for_line(line)

            # 启动后台线程
            thread = threading.Thread(target=preview_in_background, daemon=True)
            thread.start()

        except Exception as e:
            print(f"试听音频失败: {e}")
            if hasattr(line, '_audio_track_info'):
                line._audio_track_info['playback_active'] = False
                self.reset_playback_progress_for_line(line)
            self.show_snack_bar(f"试听失败: {str(e)[:100]}")

    def start_playback_progress_animation_for_line(self, line, duration):
        """为特定行开始播放进度动画"""
        import time

        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info
        canvas_width = audio_info['canvas'].width if audio_info['canvas'] else 340
        audio_info['playback_start_time'] = time.time()

        def update_progress():
            if not audio_info.get('playback_active', False):
                return

            try:
                elapsed = time.time() - audio_info['playback_start_time']
                progress = min(elapsed / duration, 1.0)

                # 计算当前位置
                current_pos = progress * canvas_width

                # 更新进度指示器位置
                if audio_info['progress_indicator']:
                    audio_info['progress_indicator'].left = current_pos

                    # 更新时间显示
                    if audio_info['timeline_text']:
                        current_time = progress * audio_info['total_duration'] if audio_info[
                                                                                      'total_duration'] > 0 else elapsed
                        minutes = int(current_time // 60)
                        seconds = int(current_time % 60)
                        total_minutes = int(audio_info['total_duration'] // 60)
                        total_seconds = int(audio_info['total_duration'] % 60)
                        time_text = f"{minutes:02d}:{seconds:02d} / {total_minutes:02d}:{total_seconds:02d}"
                        audio_info['timeline_text'].value = time_text

                # 更新UI
                if audio_info['progress_indicator']:
                    audio_info['progress_indicator'].update()
                if audio_info['timeline_text']:
                    audio_info['timeline_text'].update()

                # 如果未完成，继续更新
                if progress < 1.0 and audio_info.get('playback_active', False):
                    # 延迟50ms后再次更新
                    threading.Timer(0.05, update_progress).start()
                else:
                    # 播放完成
                    audio_info['playback_active'] = False

            except Exception as e:
                print(f"更新播放进度失败: {e}")

        # 开始动画
        update_progress()

    def reset_playback_progress_for_line(self, line):
        """重置特定行的播放进度"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info
        audio_info['playback_active'] = False

        try:
            if audio_info['progress_indicator']:
                audio_info['progress_indicator'].opacity = 0
                audio_info['progress_indicator'].left = 0
                audio_info['progress_indicator'].update()

            # 重置时间显示
            if audio_info['timeline_text'] and audio_info.get('total_duration', 0) > 0:
                total_minutes = int(audio_info['total_duration'] // 60)
                total_seconds = int(audio_info['total_duration'] % 60)
                audio_info['timeline_text'].value = f"00:00 / {total_minutes:02d}:{total_seconds:02d}"
                audio_info['timeline_text'].update()
        except Exception as e:
            print(f"重置播放进度失败: {e}")

    def start_playback_progress_animation(self, duration):
        """开始播放进度动画 - 使用定时器更新"""
        import time

        # 获取Canvas宽度
        if not hasattr(self, 'progress_indicator') or not hasattr(self, 'waveform_canvas_ref'):
            return

        canvas_width = self.waveform_canvas_ref.width

        # 记录开始时间
        self.playback_start_time = time.time()

        # 定义一个更新函数
        def update_progress():
            if not self.playback_active:
                return

            elapsed = time.time() - self.playback_start_time
            progress = min(elapsed / duration, 1.0)

            # 计算当前位置
            current_pos = progress * canvas_width

            # 更新进度指示器位置
            if hasattr(self, 'progress_indicator'):
                self.progress_indicator.left = current_pos

                # 更新时间显示
                if hasattr(self, 'timeline_text'):
                    current_time = progress * self.total_duration if self.total_duration > 0 else elapsed
                    minutes = int(current_time // 60)
                    seconds = int(current_time % 60)
                    total_minutes = int(self.total_duration // 60)
                    total_seconds = int(self.total_duration % 60)
                    time_text = f"{minutes:02d}:{seconds:02d} / {total_minutes:02d}:{total_seconds:02d}"
                    self.timeline_text.value = time_text

            # 更新UI
            try:
                if hasattr(self, 'progress_indicator'):
                    self.progress_indicator.update()
                if hasattr(self, 'timeline_text'):
                    self.timeline_text.update()
            except Exception as e:
                print(f"更新UI失败: {e}")

            # 如果未完成，继续更新
            if progress < 1.0 and self.playback_active:
                # 使用page的post方法延迟执行下一次更新
                if hasattr(self.page, 'post'):
                    self.page.post(update_progress, delay=50)  # 50ms后再次更新
                else:
                    # 如果没有post方法，使用线程延迟
                    threading.Timer(0.05, update_progress).start()
            else:
                # 播放完成
                self.playback_active = False
                self.reset_playback_progress()

        # 开始动画
        update_progress()

    def reset_playback_progress(self):
        """重置播放进度"""
        self.playback_active = False

        # 直接在UI线程中更新
        try:
            if hasattr(self, 'progress_indicator'):
                self.progress_indicator.opacity = 0
                self.progress_indicator.left = 0
                self.progress_indicator.update()

            # 重置时间显示
            if hasattr(self, 'timeline_text') and hasattr(self, 'total_duration') and self.total_duration > 0:
                total_minutes = int(self.total_duration // 60)
                total_seconds = int(self.total_duration % 60)
                self.timeline_text.value = f"00:00 / {total_minutes:02d}:{total_seconds:02d}"
                self.timeline_text.update()
        except Exception as e:
            print(f"重置播放进度失败: {e}")

    def get_audio_duration(self, file_path):
        """获取音频文件时长"""
        try:
            import wave
            with wave.open(file_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                return frames / float(rate)
        except:
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(file_path)
                return len(audio) / 1000.0
            except:
                return 0

    def cleanup_temp_file(self, file_path, max_retries=10, initial_delay=0.5):
        """清理临时文件，支持重试"""
        if not os.path.exists(file_path):
            print(f"文件不存在，无需清理: {file_path}")
            return True

        for attempt in range(max_retries):
            try:
                # 尝试删除文件
                os.remove(file_path)
                print(f"成功清理临时文件: {file_path} (第{attempt + 1}次尝试)")
                return True

            except PermissionError:
                # 文件被占用，等待后重试
                if attempt < max_retries - 1:
                    wait_time = initial_delay * (2 ** attempt)  # 指数退避
                    print(f"文件被占用，等待 {wait_time:.1f}秒后重试: {file_path}")
                    time.sleep(wait_time)
                else:
                    print(f"无法删除文件，可能仍在占用: {file_path}")
                    # 最后尝试，强制等待更长时间
                    time.sleep(2)
                    try:
                        os.remove(file_path)
                        print(f"最终重试成功清理: {file_path}")
                        return True
                    except:
                        return False

            except FileNotFoundError:
                # 文件已被删除
                print(f"文件已不存在: {file_path}")
                return True

            except Exception as e:
                print(f"清理文件失败 {file_path}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(initial_delay)

        return False

    def cleanup_on_exit(self, file_path):
        """程序退出时清理文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"程序退出时清理文件: {file_path}")
        except:
            pass  # 忽略退出时的清理错误

    def apply_audio_processing(self, line, speed, volume, on_success_callback=None):
        """应用音频处理到原文件"""
        print(f"apply_audio_processing 被调用: line={line.id}, speed={speed}, volume={volume}")

        if not hasattr(line, 'audio_path') or not line.audio_path:
            self.show_snack_bar("音频文件不存在")
            return

        if not os.path.exists(line.audio_path):
            self.show_snack_bar("音频文件不存在，请先生成语音")
            return

        try:
            # 检查ffmpeg是否可用
            if not self.check_ffmpeg_available():
                self.show_snack_bar("错误: FFmpeg未安装或不可用")
                return

            # 直接显示处理提示
            self.show_snack_bar(f"正在应用处理: 速度{speed:.1f}x, 音量{volume}%...")
            print("开始直接处理音频")

            # 在后台线程中处理音频
            def apply_in_background():
                try:
                    print("后台线程开始处理")
                    success = self.process_audio_with_ffmpeg(line, speed, volume)
                    print(f"处理结果: {success}")

                    # 在主线程中处理结果
                    def handle_result():
                        try:
                            print("主线程处理结果")
                            if success:
                                try:
                                    print("保存设置到数据库")
                                    # 保存设置到数据库
                                    self.line_controller.update_line(
                                        line.id,
                                        speed=float(speed),
                                        volume=float(volume)
                                    )
                                    print("设置保存成功")
                                    self.show_snack_bar("✅ 音频处理完成！设置已保存")

                                    # 执行重置滑块的回调
                                    if on_success_callback:
                                        print("执行重置回调")
                                        on_success_callback()

                                    print("刷新列表")
                                    # 刷新列表
                                    self.load_lines(self.current_chapter)
                                    print("刷新完成")

                                except Exception as e:
                                    print(f"保存设置失败: {e}")
                                    self.show_snack_bar("⚠️ 音频处理完成，但保存设置失败")
                            else:
                                print("音频处理失败")
                                self.show_snack_bar("❌ 音频处理失败")

                        except Exception as e:
                            print(f"主线程处理异常: {e}")
                            self.show_snack_bar(f"❌ 处理失败: {str(e)}")

                    # 在Flet中，使用page.add()来触发UI线程更新
                    self.page.add(ft.Container(width=0, height=0))
                    handle_result()
                    print("主线程更新完成")

                except Exception as e:
                    print(f"后台处理异常: {e}")
                    import traceback
                    traceback.print_exc()

                    def show_error():
                        try:
                            self.show_snack_bar(f"❌ 处理失败: {str(e)}")
                        except:
                            pass

                    # 使用相同方式在主线程显示错误
                    self.page.add(ft.Container(width=0, height=0))
                    show_error()

            # 启动后台线程
            print("启动后台线程")
            thread = threading.Thread(target=apply_in_background, daemon=True)
            thread.start()
            print("线程已启动")

        except Exception as e:
            print(f"apply_audio_processing异常: {e}")
            self.show_snack_bar(f"❌ 处理失败: {str(e)}")

    def process_audio_with_ffmpeg(self, line, speed, volume):
        """使用FFmpeg处理音频"""
        try:
            import time

            # 准备参数
            speed_value = float(speed)
            volume_value = float(volume) / 100.0  # 转换为0-3范围

            print(f"处理音频: 文件={line.audio_path}, 速度={speed_value}x, 音量={volume_value}")

            # 检查输入文件是否存在
            if not os.path.exists(line.audio_path):
                print(f"错误: 输入文件不存在: {line.audio_path}")
                return False

            # 获取输入文件大小
            input_size = os.path.getsize(line.audio_path)
            print(f"输入文件大小: {input_size} 字节")

            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time() * 1000)
            temp_path = os.path.join(temp_dir, f"processed_{line.id}_{timestamp}.wav")

            print(f"临时文件路径: {temp_path}")

            # 构建FFmpeg命令
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", line.audio_path,
                "-filter:a", f"atempo={speed_value},volume={volume_value}",
                "-ac", "2",
                "-ar", "44100",
                "-acodec", "pcm_s16le",
                temp_path
            ]

            print(f"FFmpeg命令: {' '.join(ffmpeg_cmd)}")

            # 执行FFmpeg命令
            try:
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
            except UnicodeDecodeError:
                # 如果utf-8失败，使用二进制模式读取
                result = subprocess.run(
                    ffmpeg_cmd,
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                # 尝试解码输出
                try:
                    stdout = result.stdout.decode('utf-8', errors='ignore')
                    stderr = result.stderr.decode('utf-8', errors='ignore')
                except:
                    stdout = ""
                    stderr = ""
                result = subprocess.CompletedProcess(
                    args=ffmpeg_cmd,
                    returncode=result.returncode,
                    stdout=stdout,
                    stderr=stderr
                )

            # 记录FFmpeg输出
            if result.stdout:
                print(f"FFmpeg标准输出: {result.stdout[:500]}")
            if result.stderr:
                print(f"FFmpeg错误输出: {result.stderr[:500]}")

            if result.returncode == 0:
                # 检查输出文件是否存在
                if os.path.exists(temp_path):
                    file_size = os.path.getsize(temp_path)
                    print(f"处理成功，临时文件大小: {file_size} 字节")

                    if file_size > 0:
                        # 备份原文件
                        backup_path = line.audio_path + f".backup_{timestamp}"
                        try:
                            shutil.copy2(line.audio_path, backup_path)
                            print(f"原文件已备份到: {backup_path}")
                        except Exception as e:
                            print(f"备份失败: {e}")
                            # 继续处理，备份不是必须的

                        # 替换原文件
                        try:
                            shutil.copy2(temp_path, line.audio_path)
                            print(f"文件替换完成: {line.audio_path}")

                            # 验证替换后的文件
                            if os.path.exists(line.audio_path):
                                new_size = os.path.getsize(line.audio_path)
                                print(f"新文件大小: {new_size} 字节")
                                if new_size > 0:
                                    print("音频处理成功")
                                else:
                                    print("警告: 新文件大小为0字节")
                                    # 尝试恢复备份
                                    if os.path.exists(backup_path):
                                        shutil.copy2(backup_path, line.audio_path)
                                        print("已从备份恢复原文件")
                                        return False
                            else:
                                print("错误: 替换后文件不存在")
                                return False

                        except Exception as e:
                            print(f"文件替换失败: {e}")
                            # 尝试恢复备份
                            if os.path.exists(backup_path):
                                try:
                                    shutil.copy2(backup_path, line.audio_path)
                                    print("已从备份恢复原文件")
                                except:
                                    print("恢复备份失败")
                            return False

                        # 清理临时文件
                        try:
                            os.remove(temp_path)
                            print(f"清理临时文件: {temp_path}")
                        except Exception as e:
                            print(f"清理临时文件失败: {e}")

                        # 尝试清理备份文件（可选）
                        try:
                            if os.path.exists(backup_path):
                                os.remove(backup_path)
                                print(f"清理备份文件: {backup_path}")
                        except:
                            pass  # 备份文件清理失败没关系

                        return True  # 成功返回True
                    else:
                        print(f"错误: 生成的临时文件大小为0字节")
                        # 清理无效的临时文件
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        return False
                else:
                    print(f"错误: 临时文件不存在: {temp_path}")
                    return False
            else:
                print(f"FFmpeg处理失败，返回码: {result.returncode}")
                error_msg = result.stderr[:500] if result.stderr else "无错误信息"
                print(f"FFmpeg错误输出: {error_msg}")

                # 如果存在临时文件，清理它
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass

                return False

        except FileNotFoundError:
            print("错误: 找不到ffmpeg命令。请确保ffmpeg已安装并添加到系统PATH中。")
            self.show_snack_bar("错误: 找不到ffmpeg命令，请检查安装")
            return False
        except Exception as e:
            print(f"音频处理异常: {e}")
            import traceback
            traceback.print_exc()

            # 清理可能创建的临时文件
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass

            return False

    def check_ffmpeg_available(self):
        """检查FFmpeg是否可用"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def create_export_menu(self):
        return ft.PopupMenuButton(
            content=ft.Text("📤 导出", size=12),  # 减小字体
            items=[
                ft.PopupMenuItem(text="导出到本地", on_click=lambda _: self.export_chapter_local()),
                ft.PopupMenuItem(text="导出到创作中", on_click=lambda _: self.export_chapter_creation()),
            ]
        )

    # ==================== 数据加载方法 ====================

    def load_chapters(self):
        """加载章节数据"""
        print(f"正在加载项目 {getattr(self.project, 'id', '未知')} 的章节...")
        if self.project and hasattr(self.project, 'id'):
            try:
                chapters = self.chapter_controller.get_chapters_by_project(self.project.id)
                print(f"成功加载 {len(chapters)} 个章节")
                self.update_chapter_list(chapters)
            except Exception as e:
                print(f"加载章节失败: {e}")
                self.show_snack_bar("加载章节失败")
        else:
            print("项目ID不存在，无法加载章节")
            self.show_snack_bar("项目信息不完整，无法加载章节")

    def load_roles(self):
        """加载角色列表"""
        try:
            self.roles_data = self.role_controller.get_roles_by_project(self.project.id)
        except Exception as e:
            print(f"加载角色列表失败: {e}")
            self.roles_data = []

    def update_chapter_list(self, chapters):
        """更新章节列表显示"""
        self.chapter_listview.controls.clear()

        if not chapters:
            # 如果没有章节，显示提示信息
            self.chapter_listview.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.INFO, size=24, color=ft.Colors.GREY_400),  # 减小图标
                        ft.Text("暂无章节", size=14, color=ft.Colors.GREY_500),  # 减小字体
                        ft.Text("点击添加按钮创建章节", size=11, color=ft.Colors.GREY_400)  # 减小字体
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=15,  # 减少padding
                    alignment=ft.alignment.center
                )
            )
        else:
            for chapter in chapters:
                chapter_card = self.create_chapter_card(chapter)
                self.chapter_listview.controls.append(chapter_card)

        self.page.update()

    def create_chapter_card(self, chapter):
        """创建章节卡片"""
        chapter_name = getattr(chapter, 'title', '未命名章节') or getattr(chapter, 'name', '未命名章节')
        chapter_id = getattr(chapter, 'id', None)
        # 获取台词数量
        try:
            lines = self.line_controller.get_lines_by_chapter(chapter.id)
            lines_count = len(lines)
        except:
            lines_count = 0

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("📖", size=14),  # 减小图标
                        ft.Text(
                            chapter_name,
                            size=12,  # 减小字体
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_GREY_900,
                            expand=True
                        )
                    ]),
                    ft.Text(
                        f"台词: {lines_count} 条",
                        size=10,  # 减小字体
                        color=ft.Colors.GREY_700
                    )
                ]),
                padding=8,  # 减少padding
                on_click=lambda e, c=chapter: self.select_chapter(c)
            ),
            elevation=1,  # 减小阴影
            margin=3  # 减少margin
        )

    def select_chapter(self, chapter):
        """选择章节"""
        self.current_chapter = chapter
        self.current_chapter_id = getattr(chapter, 'id', None)
        self.chapter_status_text.value = f"当前章节: {getattr(chapter, 'title', '未命名') or getattr(chapter, 'name', '未命名')}"
        self.load_chapter_content(chapter)
        self.load_lines(chapter)
        self.page.update()

    def load_chapter_content(self, chapter):
        """加载章节内容"""
        content = getattr(chapter, 'text_content', '') or getattr(chapter, 'content', '')
        self.chapter_content_field.value = content if content else "本章节暂无内容，请从文本导入"
        self.page.update()

    def load_lines(self, chapter):
        """加载台词列表"""
        if not self.current_chapter_id:
            self.show_snack_bar("请先选择章节")
            return

        try:
            lines = self.line_controller.get_lines_by_chapter(self.current_chapter_id)
            print(f"加载到 {len(lines)} 条台词")
            self.update_editable_lines_table(lines)
        except Exception as e:
            print(f"加载台词失败: {e}")
            self.show_snack_bar("加载台词失败")

    def update_editable_lines_table(self, lines):
        """更新可编辑台词表格"""
        self.editable_lines_list.controls.clear()

        if not lines:
            # 如果没有台词，显示提示信息
            self.editable_lines_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=40, color=ft.Colors.GREY_400),  # 减小图标
                        ft.Text("暂无台词", size=14, color=ft.Colors.GREY_500),  # 减小字体
                        ft.Text("点击添加按钮创建台词", size=12, color=ft.Colors.GREY_400),  # 减小字体
                        ft.ElevatedButton(
                            text="添加第一条台词",
                            icon=ft.Icons.ADD,
                            on_click=self.add_new_line,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.BLUE_600,
                                color=ft.Colors.WHITE,
                                padding=ft.padding.symmetric(15, 8)  # 减少padding
                            )
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=30,  # 减少padding
                    alignment=ft.alignment.center
                )
            )
        else:
            for i, line in enumerate(lines):
                editable_row = self.create_editable_line_row(line, i + 1)
                self.editable_lines_list.controls.append(editable_row)

        self.page.update()

    def save_line_inline(self, line, text_field, role_dropdown, emotion_dropdown, strength_dropdown):
        """内联保存台词"""
        try:
            # 获取编辑后的值
            text_content = text_field.value.strip()
            if not text_content:
                self.show_snack_bar("台词内容不能为空")
                return

            role_name = role_dropdown.value
            if not role_name:
                self.show_snack_bar("请选择角色")
                return

            # 获取或创建角色
            role = next((r for r in self.roles_data if r.name == role_name), None)

            if not role:
                role = self.role_controller.create_role(self.project.id, role_name)
                self.roles_data.append(role)  # 添加到本地数据

            # 准备更新数据
            update_data = {
                'role_id': role.id,
                'text_content': text_content,
                'emotion_id': self.get_emotion_id(emotion_dropdown.value),
                'strength_id': self.get_strength_id(strength_dropdown.value)
            }

            # 更新台词
            self.line_controller.update_line(line.id, **update_data)
            self.show_snack_bar("台词保存成功")

            # 刷新列表
            self.load_lines(self.current_chapter)

        except Exception as e:
            print(f"保存台词失败: {e}")
            self.show_snack_bar(f"保存失败: {str(e)}")

    def add_new_line(self, e):
        """添加新台词行"""
        if not self.current_chapter_id:
            self.show_snack_bar("请先选择章节")
            return

        try:
            # 创建新台词
            new_line = self.line_controller.create_line(
                chapter_id=self.current_chapter_id,
                text_content="",
                role_id=None,
                emotion_id=8,  # 默认平静
                strength_id=3  # 默认中等
            )

            self.show_snack_bar("新台词已添加")
            self.load_lines(self.current_chapter)

        except Exception as e:
            print(f"添加台词失败: {e}")
            self.show_snack_bar(f"添加失败: {str(e)}")

    def delete_single_line(self, line):
        """删除单条台词"""

        def confirm_delete(e):
            try:
                self.line_controller.delete_line(line.id)
                self.show_snack_bar("台词删除成功")
                self.load_lines(self.current_chapter)
            except Exception as e:
                self.show_snack_bar(f"删除失败: {str(e)}")
            finally:
                self.page.dialog.open = False
                self.page.update()

        def cancel_delete(e):
            self.page.dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("确认删除"),
            content=ft.Text("确定要删除这条台词吗？此操作不可撤销。"),
            actions=[
                ft.TextButton("取消", on_click=cancel_delete),
                ft.TextButton("删除", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED_600)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    # ==================== 辅助方法 ====================

    def get_role_name(self, role_id):
        """获取角色名称"""
        if not role_id:
            return "旁白"
        try:
            role = next((r for r in self.roles_data if r.id == role_id), None)
            return getattr(role, 'name', '未知') if role else "未知"
        except:
            return "未知"

    def get_emotion_name(self, emotion_id):
        """获取情绪名称"""
        emotion_map = {
            1: '高兴', 2: '生气', 3: '伤心', 4: '害怕',
            5: '厌恶', 6: '低落', 7: '惊喜', 8: '平静'
        }
        return emotion_map.get(emotion_id, '平静')

    def get_strength_name(self, strength_id):
        """获取强度名称"""
        strength_map = {
            1: '微弱', 2: '稍弱', 3: '中等', 4: '较强', 5: '强烈'
        }
        return strength_map.get(strength_id, '中等')

    def get_status_display(self, status):
        """转换状态显示"""
        status_map = {
            'pending': '未生成',
            'processing': '生成中',
            'done': '已生成',
            'failed': '生成失败'
        }
        return status_map.get(status, '未知')

    def get_status_color(self, status):
        """获取状态颜色"""
        color_map = {
            'pending': ft.Colors.ORANGE,
            'processing': ft.Colors.BLUE,
            'done': ft.Colors.GREEN,
            'failed': ft.Colors.RED
        }
        return color_map.get(status, ft.Colors.GREY)

    def get_emotion_id(self, emotion_name):
        """获取情绪ID"""
        emotion_map = {
            '高兴': 1, '生气': 2, '伤心': 3, '害怕': 4,
            '厌恶': 5, '低落': 6, '惊喜': 7, '平静': 8
        }
        return emotion_map.get(emotion_name, 8)

    def get_strength_id(self, strength_name):
        """获取强度ID"""
        strength_map = {
            '微弱': 1, '稍弱': 2, '中等': 3, '较强': 4, '强烈': 5
        }
        return strength_map.get(strength_name, 3)

    # ==================== 事件处理方法 ====================

    def go_back(self, e):
        if self.on_back_callback:
            self.on_back_callback()

    def open_project_settings(self, e):
        self.show_snack_bar("项目设置功能开发中...")

    def add_chapter(self, e):
        self.show_snack_bar("添加章节功能开发中...")

    def import_text_with_parsing(self, e):
        self.show_snack_bar("文本导入功能开发中...")

    def batch_generate_audio(self, e):
        self.show_snack_bar("批量生成功能开发中...")

    def preview_line(self, line):
        """预览台词"""
        self.show_snack_bar("预览台词功能开发中...")

    def generate_single_audio(self, line):
        """为单条台词生成音频"""
        self.show_snack_bar("生成音频功能开发中...")

    def export_chapter_local(self):
        self.show_snack_bar("导出到本地功能开发中...")

    def export_chapter_creation(self):
        self.show_snack_bar("导出到创作中功能开发中...")

    def show_snack_bar(self, message):
        """显示消息提示"""
        print(f"显示snackbar: {message}")

        try:
            # 创建snackbar
            snack_bar = ft.SnackBar(
                content=ft.Text(message),
                duration=2000,
                dismiss_direction=ft.DismissDirection.DOWN
            )

            # 清理可能存在的旧snackbar
            snackbars_to_remove = []
            for i, control in enumerate(self.page.overlay):
                if isinstance(control, ft.SnackBar):
                    snackbars_to_remove.append(i)

            # 从后往前删除，避免索引问题
            for i in reversed(snackbars_to_remove):
                if i < len(self.page.overlay):
                    del self.page.overlay[i]

            # 添加新的snackbar
            self.page.overlay.append(snack_bar)
            self.page.update()  # 先更新页面
            snack_bar.open = True
            self.page.update()  # 再更新页面显示snackbar

        except Exception as e:
            print(f"显示snackbar失败: {e}")
            # 尝试简单方式
            try:
                snack_bar = ft.SnackBar(ft.Text(message))
                self.page.snack_bar = snack_bar
                self.page.update()
            except:
                pass

    # ==================== 音频轨道相关方法 ====================

    def create_audio_track_viewer(self, line, width=360, height=80):
        """创建音频轨道查看器 - 支持区域选择"""
        # 检查音频文件是否存在
        if not hasattr(line, 'audio_path') or not line.audio_path or not os.path.exists(line.audio_path):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.AUDIO_FILE_OFF, size=24, color=ft.Colors.GREY_400),
                    ft.Text("无音频文件", size=10, color=ft.Colors.GREY_500)
                ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=width,
                height=height,
                bgcolor=ft.Colors.GREY_100,
                border_radius=5
            )

        # 创建Canvas
        canvas = cv.Canvas(
            width=width - 20,
            height=height - 30,
            expand=False
        )

        # 时间轴容器
        timeline_text = ft.Text("00:00 / 00:00", size=9, color=ft.Colors.BLUE_GREY_700)

        # 播放进度指示器
        progress_indicator = ft.Container(
            width=2,
            height=height - 30,
            bgcolor=ft.Colors.RED_600,
            left=0,
            top=0,
            opacity=0,
            animate_position=300,
            border_radius=1,
        )

        # 选择区域指示器
        selection_rect = ft.Container(
            width=0,
            height=height - 30,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLUE_400),
            left=0,
            top=0,
            opacity=0,  # 默认隐藏
            border=ft.border.all(1, ft.Colors.BLUE_600),
        )

        # 选择时间显示
        selection_time_text = ft.Text("未选择区域", size=13, color=ft.Colors.BLUE_700)

        # 使用Stack叠加所有图层
        canvas_with_overlays = ft.Stack(
            [
                canvas,
                selection_rect,  # 选择区域在最上层
                progress_indicator,  # 播放进度在中间
            ],
            width=width - 20,
            height=height - 30,
        )

        # 音频轨道容器 - 修复：添加鼠标拖拽事件
        audio_track = ft.Container(
            content=ft.Column([
                canvas_with_overlays,
                ft.Container(
                    content=timeline_text,
                    width=width,
                    height=16,
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.BLUE_GREY_50,
                ),
            ], spacing=0),
            width=width,
            height=height - 16,
            bgcolor=ft.Colors.WHITE,
            border_radius=5,
            alignment=ft.alignment.center,
            # 修复：使用 GestureDetector 来处理鼠标拖拽
            on_hover=lambda e: self.on_wave_hover(e, line, width),
        )

        # 创建手势检测器来包装容器
        gesture_detector = ft.GestureDetector(
            content=audio_track,
            mouse_cursor=ft.MouseCursor.CLICK,
            on_tap_down=lambda e, w=width: self.on_wave_tap_down(e, line, w),  # 传递宽度参数
            on_pan_start=lambda e, w=width: self.on_wave_pan_start(e, line, w),  # 传递宽度参数
            on_pan_update=lambda e, w=width: self.on_wave_pan_update(e, line, w),  # 传递宽度参数
            on_pan_end=lambda e, w=width: self.on_wave_pan_end(e, line, w),  # 传递宽度参数
            on_double_tap=lambda e, w=width: self.on_wave_double_tap(e, line, w),  # 传递宽度参数
            # on_secondary_tap_down=lambda e, w=width: self.on_wave_right_click(e, line, w),  # 传递宽度参数
        )

        # 为这行音频存储独立的引用
        line_audio_info = {
            'canvas': canvas,
            'progress_indicator': progress_indicator,
            'selection_rect': selection_rect,
            'timeline_text': timeline_text,
            'selection_time_text': selection_time_text,
            'playback_active': False,
            'total_duration': 0,
            'selection_start': None,
            'selection_end': None,
            'is_selecting': False,
            'drag_start_x': None,
            'canvas_width': width - 20,  # 存储画布宽度
            'container_width': width,  # 存储容器宽度
        }

        # 将引用存储在line对象上
        line._audio_track_info = line_audio_info

        # 使用定时器延迟加载波形
        def delayed_load():
            import time
            time.sleep(0.5)
            self._load_and_draw_waveform_sync(line, canvas)

        threading.Thread(target=delayed_load, daemon=True).start()

        return gesture_detector  # 返回手势检测器

    # 修改鼠标事件方法，添加宽度参数
    def on_wave_tap_down(self, e, line, width):
        """鼠标按下事件"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info

        # 获取点击位置
        x = e.local_x if hasattr(e, 'local_x') else 0
        track_width = width - 20  # 使用传递的宽度参数

        # 确保x在有效范围内
        x = max(0, min(x, track_width))

        # 判断是否在现有选择区域内点击
        if audio_info['selection_start'] is not None and audio_info['selection_end'] is not None:
            start_x = min(audio_info['selection_start'], audio_info['selection_end'])
            end_x = max(audio_info['selection_start'], audio_info['selection_end'])

            if start_x <= x <= end_x:
                # 在现有选择区域内点击，开始拖拽整个选区
                audio_info['is_dragging_selection'] = True
                audio_info['drag_offset'] = x - start_x
                return

        # 记录拖拽起始位置
        audio_info['drag_start_x'] = x
        audio_info['is_selecting'] = True
        audio_info['selection_start'] = x
        audio_info['selection_end'] = x

        # 显示选择矩形
        if audio_info['selection_rect']:
            audio_info['selection_rect'].width = 0
            audio_info['selection_rect'].left = x
            audio_info['selection_rect'].opacity = 1
            audio_info['selection_rect'].update()

        # 更新选择时间显示
        self.update_selection_time_display_for_line(line)

        print(f"开始选择: x={x}")

    def on_wave_pan_start(self, e, line, width):
        """开始拖拽"""
        self.on_wave_tap_down(e, line, width)

    def on_wave_pan_update(self, e, line, width):
        """拖拽更新"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info

        if not audio_info.get('is_selecting', False) and not audio_info.get('is_dragging_selection', False):
            return

        # 获取当前鼠标位置
        x = e.local_x if hasattr(e, 'local_x') else 0
        track_width = width - 20  # 使用传递的宽度参数

        # 确保x在有效范围内
        x = max(0, min(x, track_width))

        if audio_info.get('is_dragging_selection', False):
            # 拖拽整个选区
            if audio_info['selection_start'] is not None and audio_info['selection_end'] is not None:
                start_x = min(audio_info['selection_start'], audio_info['selection_end'])
                end_x = max(audio_info['selection_start'], audio_info['selection_end'])
                selection_width = end_x - start_x

                # 计算新的位置
                new_start = x - audio_info['drag_offset']
                new_start = max(0, min(new_start, track_width - selection_width))
                new_end = new_start + selection_width

                audio_info['selection_start'] = new_start
                audio_info['selection_end'] = new_end
        else:
            # 更新选择结束位置
            audio_info['selection_end'] = x

        # 更新选择矩形
        if audio_info['selection_rect']:
            start_x = min(audio_info['selection_start'], audio_info['selection_end'])
            end_x = max(audio_info['selection_start'], audio_info['selection_end'])
            audio_info['selection_rect'].left = start_x
            audio_info['selection_rect'].width = end_x - start_x
            audio_info['selection_rect'].update()

        # 更新选择时间显示
        self.update_selection_time_display_for_line(line)

    def on_wave_pan_end(self, e, line, width):
        """结束拖拽"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info

        # 获取结束位置
        x = e.local_x if hasattr(e, 'local_x') else 0
        track_width = width - 20  # 使用传递的宽度参数
        x = max(0, min(x, track_width))

        if audio_info.get('is_dragging_selection', False):
            # 结束拖拽选区
            audio_info['is_dragging_selection'] = False
            self.show_snack_bar("选区已移动")
        elif audio_info.get('is_selecting', False):
            # 结束选择
            audio_info['is_selecting'] = False

            # 如果选择区域太小，清除选择
            start_x = min(audio_info['selection_start'], audio_info['selection_end'])
            end_x = max(audio_info['selection_start'], audio_info['selection_end'])

            if abs(end_x - start_x) < 5:  # 5像素的最小选择宽度
                self.clear_selection_for_line(line)
                self.show_snack_bar("选择区域太小，已清除")
            else:
                # 计算并打印选中时间
                # 在 on_wave_pan_end 方法中，修改时间显示部分：
                if audio_info['total_duration'] > 0:
                    start_time = (start_x / track_width) * audio_info['total_duration']
                    end_time = (end_x / track_width) * audio_info['total_duration']

                    # 格式化时间函数
                    def format_time(seconds):
                        minutes = int(seconds // 60)
                        secs = seconds % 60
                        secs_int = int(secs)
                        secs_frac = int((secs - secs_int) * 10)  # 取一位小数
                        return f"{minutes:02d}:{secs_int:02d}.{secs_frac}"

                    start_str = format_time(start_time)
                    end_str = format_time(end_time)
                    dur_str = format_time(end_time - start_time)

                    # 打印选中时间区域
                    print(f"选中时间区域: {start_str} - {end_str} (时长: {dur_str})")

                    # 显示给用户
                    self.show_snack_bar(f"选中: {start_str} - {end_str}")
                else:
                    self.show_snack_bar("音频时长未知，无法计算时间")

        # 清除拖拽状态
        audio_info['drag_start_x'] = None

    def on_wave_double_tap(self, e, line, width):
        """双击事件"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info

        # 获取双击位置
        x = e.local_x if hasattr(e, 'local_x') else 0
        track_width = width - 20  # 使用传递的宽度参数
        x = max(0, min(x, track_width))

        # 清除现有选择
        self.clear_selection_for_line(line)

        # 开始新的选择
        audio_info['is_selecting'] = True
        audio_info['selection_start'] = x
        audio_info['selection_end'] = x

        # 显示选择矩形
        if audio_info['selection_rect']:
            audio_info['selection_rect'].width = 0
            audio_info['selection_rect'].left = x
            audio_info['selection_rect'].opacity = 1
            audio_info['selection_rect'].update()

        # 更新选择时间显示
        self.update_selection_time_display_for_line(line)

        # 打印开始选择的位置
        if audio_info['total_duration'] > 0:
            start_time = (x / track_width) * audio_info['total_duration']
            print(f"开始选择于: {start_time:.2f}s")

        self.show_snack_bar("双击开始选择，移动鼠标调整范围")

    def on_wave_right_click(self, e, line, width):
        """右键点击事件 - 显示操作菜单"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info

        # 检查是否有选择区域
        has_selection = (audio_info['selection_start'] is not None and
                         audio_info['selection_end'] is not None and
                         audio_info['total_duration'] > 0)

        # 创建右键菜单
        menu_items = []

        if has_selection:
            # 如果有选择区域，显示选区操作
            track_width = width - 20  # 使用传递的宽度参数
            start_px = min(audio_info['selection_start'], audio_info['selection_end'])
            end_px = max(audio_info['selection_start'], audio_info['selection_end'])
            start_time = (start_px / track_width) * audio_info['total_duration']
            end_time = (end_px / track_width) * audio_info['total_duration']

            menu_items.extend([
                ft.PopupMenuItem(
                    text=f"播放选区 ({start_time:.1f}s - {end_time:.1f}s)",
                    on_click=lambda ev, l=line, s=start_time, et=end_time: self.play_audio_selection(l, s, et)
                ),
                ft.PopupMenuItem(
                    text="裁剪选区为新文件",
                    on_click=lambda ev, l=line, s=start_time, et=end_time: self.crop_audio_selection(l, s, et)
                ),
                ft.PopupMenuItem(),
                ft.PopupMenuItem(
                    text="清除选择",
                    on_click=lambda ev, l=line: self.clear_selection_for_line(l)
                ),
            ])
        else:
            # 如果没有选择区域
            menu_items.append(
                ft.PopupMenuItem(
                    text="双击或拖拽选择区域",

                )
            )

        # 通用操作
        menu_items.extend([
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                text="从头播放",
                on_click=lambda ev, l=line: self.play_audio_from_time(l, 0)
            ),
            ft.PopupMenuItem(
                text="停止播放",
                on_click=lambda ev: self.stop_audio_playback(ev)
            ),
            ft.PopupMenuItem(),
            ft.PopupMenuItem(
                text="查看音频信息",
                on_click=lambda ev, l=line: self.show_audio_info(l)
            ),
        ])

        # 显示菜单
        menu = ft.PopupMenuButton(
            items=menu_items
        )

        # 临时添加菜单到页面
        def show_menu():
            try:
                # 在当前点击位置显示菜单
                e.control.content = menu
                menu.open = True
                self.page.update()
            except Exception as ex:
                print(f"显示菜单失败: {ex}")
                self.show_snack_bar("显示菜单失败")

        # 延迟显示菜单，确保事件处理完成
        import threading
        threading.Timer(0.1, show_menu).start()

    # 修改 on_wave_hover 方法
    def on_wave_hover(self, e, line, width):
        """波形区域鼠标悬停 - 显示时间位置"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info

        # 检查音频数据是否存在且有效
        if audio_info['total_duration'] <= 0:
            return

        # 获取鼠标位置
        x = e.local_x if hasattr(e, 'local_x') else 0
        track_width = width - 20  # 使用传递的宽度参数

        # 确保x在有效范围内
        if x < 0 or x > track_width:
            return

        time_sec = (x / track_width) * audio_info['total_duration']

        # 更新时间提示
        minutes = int(time_sec // 60)
        seconds = int(time_sec % 60)
        total_minutes = int(audio_info['total_duration'] // 60)
        total_seconds = int(audio_info['total_duration'] % 60)

        time_text = f"{minutes:02d}:{seconds:02d} / {total_minutes:02d}:{total_seconds:02d}"

        # 更新悬停时间显示
        if audio_info['timeline_text']:
            audio_info['timeline_text'].value = time_text
            audio_info['timeline_text'].update()

    # 修改 on_wave_click 方法
    def on_wave_click(self, e, line, width):
        """波形区域点击事件 - 现在只处理简单点击"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info

        # 获取点击位置
        x = e.local_x if hasattr(e, 'local_x') else 0
        track_width = width - 20  # 使用传递的宽度参数
        x = max(0, min(x, track_width))

        # 简单点击播放
        if audio_info['total_duration'] > 0:
            start_time = (x / track_width) * audio_info['total_duration']
            self.play_audio_from_time(line, start_time)

    def _load_and_draw_waveform_sync(self, line, canvas):
        """同步加载和绘制波形（在UI线程中）"""
        try:
            print(f"同步加载音频波形: {line.audio_path}")

            import wave
            import numpy as np

            with wave.open(line.audio_path, 'rb') as wav_file:
                sample_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                duration = n_frames / float(sample_rate)

                print(f"音频时长: {duration:.2f}s")

                # 读取音频数据
                audio_data = wav_file.readframes(n_frames)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # 快速处理
                canvas_width = canvas.width
                max_points = min(canvas_width, 200)
                if len(audio_array) > max_points:
                    step = len(audio_array) // max_points
                    audio_array = audio_array[::step]

                audio_array = audio_array.astype(np.float32) / 32768.0

                # 直接绘制
                self._draw_simple_waveform(canvas, audio_array, duration)

                # 确保音频时长存储在 line 的音频信息中
                if hasattr(line, '_audio_track_info'):
                    line._audio_track_info['total_duration'] = duration
                    print(f"已设置音频时长: {duration:.2f}s")

        except Exception as e:
            print(f"同步加载失败: {e}")

            # 即使加载失败，也要设置一个默认的音频时长（比如从文件获取）
            try:
                duration = self.get_audio_duration(line.audio_path)
                if hasattr(line, '_audio_track_info'):
                    line._audio_track_info['total_duration'] = duration
                    print(f"使用get_audio_duration获取时长: {duration:.2f}s")
            except:
                if hasattr(line, '_audio_track_info'):
                    line._audio_track_info['total_duration'] = 0

    def _draw_simple_waveform(self, canvas, audio_data, duration):
        """绘制简单波形"""
        try:
            canvas_width = canvas.width
            canvas_height = canvas.height
            center_y = canvas_height / 2

            # 绘制波形
            canvas.shapes = [
                cv.Rect(
                    0, 0, canvas_width, canvas_height,
                    paint=ft.Paint(color=ft.Colors.WHITE)
                )
            ]

            if len(audio_data) > 0:
                n_points = len(audio_data)
                step = max(1, n_points // 100)

                prev_x = 0
                prev_y = center_y

                for i in range(0, n_points, step):
                    x = (i / n_points) * canvas_width
                    amplitude = max(-1.0, min(1.0, audio_data[i]))
                    y = center_y - (amplitude * center_y * 0.7)

                    if i > 0:
                        canvas.shapes.append(
                            cv.Line(
                                prev_x, prev_y,
                                x, y,
                                paint=ft.Paint(color=ft.Colors.BLUE_600, stroke_width=1)
                            )
                        )

                    prev_x = x
                    prev_y = y

            # 更新Canvas
            canvas.update()

            # 更新时间
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            time_text = f"00:00 / {minutes:02d}:{seconds:02d}"

            if hasattr(self, 'timeline_text') and self.timeline_text:
                self.timeline_text.value = time_text
                self.timeline_text.update()

            print(f"波形绘制完成: {time_text}")

        except Exception as e:
            print(f"绘制波形失败: {e}")

    def load_waveform_data_async(self, line, canvas):
        """异步加载波形数据"""
        try:
            print(f"开始加载音频波形: {line.audio_path}")

            # 读取音频文件
            import wave
            import numpy as np

            with wave.open(line.audio_path, 'rb') as wav_file:
                # 获取音频信息
                sample_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                duration = n_frames / float(sample_rate)
                n_channels = wav_file.getnchannels()

                print(f"音频信息: 采样率={sample_rate}, 帧数={n_frames}, 时长={duration:.2f}s, 声道数={n_channels}")

                # 读取音频数据
                audio_data = wav_file.readframes(n_frames)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                print(f"原始音频数据形状: {audio_array.shape}")

                # 如果是立体声，转换为单声道
                if n_channels == 2:
                    audio_array = audio_array.reshape(-1, 2)
                    audio_array = audio_array.mean(axis=1).astype(np.int16)
                    print(f"单声道转换后形状: {audio_array.shape}")

                # 降采样以减少绘制点数
                canvas_width = canvas.width
                max_points = min(canvas_width, 600)
                if len(audio_array) > max_points:
                    step = len(audio_array) // max_points
                    audio_array = audio_array[::step]
                    print(f"降采样后点数: {len(audio_array)}")

                # 归一化到0-1范围
                audio_array = audio_array.astype(np.float32) / 32768.0

                # 存储数据供后续使用
                self.waveform_data = audio_array
                self.audio_duration = duration

                # 在主线程中更新UI
                def update_ui():
                    print("=== 开始更新UI ===")
                    try:
                        # 先绘制一个简单的测试图形
                        print(f"Canvas尺寸: {canvas.width}x{canvas.height}")

                        canvas.shapes = [
                            cv.Rect(
                                0, 0, canvas.width, canvas.height,
                                paint=ft.Paint(color=ft.Colors.WHITE)
                            ),
                            cv.Line(
                                10, 10, canvas.width - 10, canvas.height - 10,
                                paint=ft.Paint(color=ft.Colors.RED, stroke_width=2)
                            ),
                            cv.Text(
                                "测试波形绘制",
                                canvas.width / 2 - 40,
                                canvas.height / 2,
                                style=ft.TextStyle(color=ft.Colors.BLUE, size=12)
                            )
                        ]
                        canvas.update()
                        print("测试绘制完成")

                        # 如果需要绘制真实波形，稍后启用
                        # self._draw_waveform_simple(canvas, audio_array)

                        # 更新时间显示
                        minutes = int(duration // 60)
                        seconds = int(duration % 60)
                        time_text = f"00:00 / {minutes:02d}:{seconds:02d}"

                        if hasattr(self, 'timeline_text') and self.timeline_text:
                            self.timeline_text.value = time_text
                            print(f"更新时间显示: {time_text}")
                            # 不需要调用update，page.add会自动更新

                        print(f"波形绘制完成，时长: {time_text}")
                    except Exception as e:
                        print(f"更新UI失败: {e}")
                        import traceback
                        traceback.print_exc()

                # 使用page.add在主线程中执行 - 确保这是正确的方式
                print("调用page.add更新UI...")
                self.page.add(ft.Container(width=0, height=0, on_click=lambda e: update_ui()))
                print("page.add已调用")

        except Exception as e:
            print(f"加载波形失败: {e}")
            import traceback
            traceback.print_exc()

            def show_error():
                try:
                    print("显示错误信息")
                    canvas.shapes = [
                        cv.Rect(
                            0, 0, canvas.width, canvas.height,
                            paint=ft.Paint(color=ft.Colors.WHITE)
                        ),
                        cv.Text(
                            "加载失败",
                            canvas.width / 2 - 20,
                            canvas.height / 2,
                            style=ft.TextStyle(color=ft.Colors.RED, size=12)
                        )
                    ]
                    canvas.update()
                except Exception as e2:
                    print(f"显示错误失败: {e2}")

            print("调用page.add显示错误...")
            self.page.add(ft.Container(width=0, height=0, on_click=lambda e: show_error()))

    def _draw_waveform_simple(self, canvas, audio_data):
        """绘制简单波形"""
        try:
            canvas_width = canvas.width
            canvas_height = canvas.height
            center_y = canvas_height / 2

            print(f"绘制波形到Canvas: {canvas_width}x{canvas_height}")

            # 清空画布
            canvas.shapes = []

            # 绘制白色背景
            canvas.shapes.append(
                cv.Rect(
                    0, 0, canvas_width, canvas_height,
                    paint=ft.Paint(color=ft.Colors.WHITE)
                )
            )

            if audio_data is None or len(audio_data) == 0:
                # 绘制空状态
                canvas.shapes.append(
                    cv.Text(
                        "无音频数据",
                        canvas_width / 2 - 25,
                        canvas_height / 2,
                        style=ft.TextStyle(color=ft.Colors.GREY_500, size=12)
                    )
                )
                canvas.update()
                return

            # 绘制波形 - 使用线段
            n_points = len(audio_data)

            # 限制绘制点数
            max_draw_points = min(300, n_points)
            step = max(1, n_points // max_draw_points)

            prev_x = 0
            prev_y = center_y

            # 绘制波形线
            for i in range(0, n_points, step):
                x = (i / n_points) * canvas_width
                amplitude = audio_data[i]
                amplitude = max(-1.0, min(1.0, amplitude))
                y = center_y - (amplitude * center_y * 0.7)

                if i > 0:
                    canvas.shapes.append(
                        cv.Line(
                            prev_x, prev_y,
                            x, y,
                            paint=ft.Paint(color=ft.Colors.BLUE_600, stroke_width=1)
                        )
                    )

                prev_x = x
                prev_y = y

            # 更新Canvas
            canvas.update()
            print("波形绘制完成")

        except Exception as e:
            print(f"绘制波形失败: {e}")
            import traceback
            traceback.print_exc()


    def on_wave_click(self, e, line):
        """波形区域点击事件 - 支持双击选择区域"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info

        # 获取点击位置
        x = e.local_x if hasattr(e, 'local_x') else 0
        track_width = audio_info['canvas'].width if audio_info['canvas'] else 340

        # 确保x在有效范围内
        if x < 0 or x > track_width:
            return

        # 检查是否是双击
        current_time = time.time()
        if hasattr(audio_info, 'last_click_time'):
            last_click_time = audio_info['last_click_time']
        else:
            last_click_time = 0

        if current_time - last_click_time < 0.3:  # 300ms内认为是双击
            # 双击开始选择区域
            self.start_selection_for_line(line, x)
            audio_info['last_click_time'] = 0  # 重置
            return

        audio_info['last_click_time'] = current_time

        # 单击播放
        if audio_info['total_duration'] > 0:
            start_time = (x / track_width) * audio_info['total_duration']
            self.play_audio_from_time(line, start_time)

    def start_selection_for_line(self, line, x):
        """为特定行开始选择区域"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info
        audio_info['is_selecting'] = True
        audio_info['selection_start'] = x
        audio_info['selection_end'] = x

        # 显示选择矩形
        if audio_info['selection_rect']:
            audio_info['selection_rect'].width = 0
            audio_info['selection_rect'].left = x
            audio_info['selection_rect'].height = audio_info['canvas'].height if audio_info['canvas'] else 50
            audio_info['selection_rect'].opacity = 1
            audio_info['selection_rect'].update()

        # 更新选择时间显示
        self.update_selection_time_display_for_line(line)

        # 绑定鼠标移动事件
        def on_mouse_move(e):
            if audio_info['is_selecting']:
                track_width = audio_info['canvas'].width if audio_info['canvas'] else 340
                x_pos = max(0, min(e.local_x if hasattr(e, 'local_x') else 0, track_width))
                audio_info['selection_end'] = x_pos

                # 更新选择矩形
                if audio_info['selection_rect']:
                    start_x = min(audio_info['selection_start'], audio_info['selection_end'])
                    end_x = max(audio_info['selection_start'], audio_info['selection_end'])
                    audio_info['selection_rect'].left = start_x
                    audio_info['selection_rect'].width = end_x - start_x
                    audio_info['selection_rect'].update()

                # 更新时间显示
                self.update_selection_time_display_for_line(line)

        # 绑定鼠标释放事件
        def on_mouse_up(e):
            if audio_info['is_selecting']:
                audio_info['is_selecting'] = False
                self.show_snack_bar("选择完成，右键菜单可操作选区")

        # 暂时绑定事件
        audio_info['_on_mouse_move'] = on_mouse_move
        audio_info['_on_mouse_up'] = on_mouse_up

        self.show_snack_bar("开始选择区域，移动鼠标调整范围，释放鼠标完成")

    # 修改 update_selection_time_display_for_line 方法：
    def update_selection_time_display_for_line(self, line):
        """更新特定行的选择时间显示 - 精确到0.1秒"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info

        if (audio_info['selection_start'] is not None and
                audio_info['selection_end'] is not None and
                audio_info['total_duration'] > 0):

            track_width = audio_info['canvas'].width if audio_info['canvas'] else 340
            start_px = min(audio_info['selection_start'], audio_info['selection_end'])
            end_px = max(audio_info['selection_start'], audio_info['selection_end'])

            start_time = (start_px / track_width) * audio_info['total_duration']
            end_time = (end_px / track_width) * audio_info['total_duration']
            duration = end_time - start_time

            # 格式化时间函数
            def format_time(seconds):
                minutes = int(seconds // 60)
                secs = seconds % 60
                # 将秒数格式化为整数部分2位，小数部分1位
                secs_int = int(secs)
                secs_frac = int((secs - secs_int) * 10)  # 取一位小数
                return f"{minutes:02d}:{secs_int:02d}.{secs_frac}"

            start_str = format_time(start_time)
            end_str = format_time(end_time)
            dur_str = format_time(duration)

            time_text = f"{start_str} - {end_str} ({dur_str})"

            if audio_info['selection_time_text']:
                audio_info['selection_time_text'].value = time_text
                audio_info['selection_time_text'].update()
        else:
            if audio_info['selection_time_text']:
                audio_info['selection_time_text'].value = "未选择区域"
                audio_info['selection_time_text'].update()

    def clear_selection_for_line(self, line):
        """清除特定行的选择"""
        if not hasattr(line, '_audio_track_info'):
            return

        audio_info = line._audio_track_info
        audio_info['selection_start'] = None
        audio_info['selection_end'] = None
        audio_info['is_selecting'] = False

        if audio_info['selection_rect']:
            audio_info['selection_rect'].opacity = 0
            audio_info['selection_rect'].update()

        self.update_selection_time_display_for_line(line)
        self.show_snack_bar("选择已清除")

    def _safe_start_selection(self, x):
        """安全地开始选择（在主线程中执行）"""
        try:
            self.is_selecting = True
            self.selection_start = x
            self.selection_end = x

            # 显示选择矩形
            if hasattr(self, 'selection_rect'):
                self.selection_rect.width = 0
                self.selection_rect.left = x
                if hasattr(self, 'audio_track_ref'):
                    self.selection_rect.height = self.audio_track_ref.height - 60
                self.selection_rect.opacity = 1
                self.selection_rect.update()

            self.show_snack_bar("开始选择区域，移动鼠标调整范围")
        except Exception as ex:
            print(f"开始选择失败: {ex}")

    def load_waveform_data(self, line, canvas):
        """加载并绘制波形数据"""
        try:
            print(f"开始加载波形数据: {line.audio_path}")

            # 读取音频文件
            import wave
            import numpy as np

            with wave.open(line.audio_path, 'rb') as wav_file:
                # 获取音频信息
                sample_rate = wav_file.getframerate()
                n_frames = wav_file.getnframes()
                duration = n_frames / float(sample_rate)
                n_channels = wav_file.getnchannels()

                print(f"音频信息: 采样率={sample_rate}, 帧数={n_frames}, 时长={duration:.2f}s, 声道数={n_channels}")

                # 读取音频数据
                audio_data = wav_file.readframes(n_frames)
                audio_array = np.frombuffer(audio_data, dtype=np.int16)

                # 如果是立体声，转换为单声道
                if n_channels == 2:
                    audio_array = audio_array.reshape(-1, 2)
                    audio_array = audio_array.mean(axis=1).astype(np.int16)

                print(f"音频数据形状: {audio_array.shape}")

                # 降采样以减少绘制点数
                canvas_width = canvas.width
                max_points = min(canvas_width, 600)  # 限制最大点数
                if len(audio_array) > max_points:
                    step = len(audio_array) // max_points
                    audio_array = audio_array[::step]
                    print(f"降采样后点数: {len(audio_array)}")

                # 归一化到0-1范围
                audio_array = audio_array.astype(np.float32) / 32768.0

                # 在主线程中更新UI
                def update_ui():
                    print(f"开始更新UI，音频数据长度: {len(audio_array)}")
                    try:
                        self._draw_waveform_simple(canvas, audio_array)
                        self._update_timeline_safe(duration)
                        print("波形绘制完成")
                    except Exception as e:
                        print(f"更新UI失败: {e}")

                # 在主线程中执行
                self.page.add(ft.Container(width=0, height=0, on_click=lambda e: update_ui()))

        except Exception as e:
            print(f"加载波形失败: {e}")
            import traceback
            traceback.print_exc()

            # 在主线程中显示错误
            def show_error():
                self._show_waveform_error(canvas)

            self.page.add(ft.Container(width=0, height=0, on_click=lambda e: show_error()))

    def _update_waveform_ui(self, canvas, audio_array, duration):
        """在主线程中更新波形UI"""
        try:
            # 存储数据
            self.waveform_data = audio_array
            self.audio_duration = duration

            # 绘制波形
            self._draw_waveform_simple(canvas, audio_array)

            # 更新时间显示
            self._update_timeline_safe(duration)

        except Exception as e:
            print(f"更新波形UI失败: {e}")

    def _show_waveform_error(self, canvas):
        """显示波形错误"""
        try:
            canvas.shapes = [
                cv.Text("波形加载失败", canvas.width / 2 - 30, canvas.height / 2, color=ft.Colors.RED)
            ]
            canvas.update()
            # 清空数据
            self.waveform_data = None
            self.audio_duration = 0
        except Exception as e:
            print(f"显示波形错误失败: {e}")

    def _update_timeline_safe(self, duration):
        """安全更新时间轴显示"""
        try:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            time_text = f"00:00 / {minutes:02d}:{seconds:02d}"

            if hasattr(self, 'timeline_text') and self.timeline_text:
                self.timeline_text.value = time_text
                self.timeline_text.update()
        except Exception as e:
            print(f"更新时间轴失败: {e}")

    def draw_waveform_with_time_grid(self, canvas, audio_data, duration):
        """绘制带时间网格的波形 - 简化版"""
        try:
            # 调用简化版的绘制方法
            self._draw_waveform_simple(canvas, audio_data)

            # 更新时间显示
            self._update_timeline_safe(duration)

            return True

        except Exception as e:
            print(f"绘制波形失败: {e}")
            return False

    def start_selection(self, x):
        """开始选择（通过双击）"""
        if self.waveform_data is None or len(self.waveform_data) == 0:
            return

        self.is_selecting = True
        self.selection_start = x
        self.selection_end = x

        # 显示选择矩形
        self.selection_rect.width = 0
        self.selection_rect.left = x
        self.selection_rect.height = self.audio_track_ref.height - 60
        self.selection_rect.opacity = 1
        self.selection_rect.update()

        self.show_snack_bar("开始选择区域，移动鼠标调整范围")

    def enable_selection_mode(self, e):
        """启用选择模式"""
        self.show_snack_bar("双击波形区域开始选择")

    def play_audio_segment(self, line):
        """播放音频（如果选择了区域，则播放选区）"""
        if not hasattr(line, 'audio_path') or not line.audio_path:
            self.show_snack_bar("音频文件不存在")
            return

        # 检查是否有选择区域
        if self.selection_start is not None and self.selection_end is not None:
            track_width = self.audio_track_ref.width
            start_px = min(self.selection_start, self.selection_end)
            end_px = max(self.selection_start, self.selection_end)

            start_time = (start_px / track_width) * self.audio_duration
            end_time = (end_px / track_width) * self.audio_duration

            # 播放选区
            self.play_audio_from_time(start_time, end_time)
            self.show_snack_bar(f"播放选区: {start_time:.1f}s - {end_time:.1f}s")
        else:
            # 播放完整音频
            self.play_audio_from_time(0, self.audio_duration)
            self.show_snack_bar("播放完整音频")

    def play_audio_from_time(self, start_time, end_time=None):
        """从指定时间开始播放音频"""
        if not hasattr(self, 'current_line'):
            return

        line = self.current_line

        try:
            # 使用模拟音频播放器
            # 停止当前播放
            audio_player.stop_audio()

            if end_time is None:
                end_time = self.audio_duration

            # 创建临时音频（从指定时间开始）
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time() * 1000)
            temp_path = os.path.join(temp_dir, f"audio_{line.id}_{timestamp}.wav")

            # 使用FFmpeg裁剪音频
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", line.audio_path,
                "-ss", str(start_time),
                "-to", str(end_time),
                "-acodec", "pcm_s16le",
                temp_path
            ]

            # 在后台处理
            def process_and_play():
                try:
                    result = subprocess.run(
                        ffmpeg_cmd,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )

                    if result.returncode == 0 and os.path.exists(temp_path):
                        # 播放音频
                        if audio_player.play_audio(temp_path):
                            # 显示播放进度
                            self.show_playback_progress(start_time, end_time)

                            # 播放完成后清理
                            def cleanup():
                                time.sleep((end_time - start_time) + 0.5)
                                if os.path.exists(temp_path):
                                    try:
                                        os.remove(temp_path)
                                    except:
                                        pass

                            threading.Thread(target=cleanup, daemon=True).start()
                        else:
                            self.show_snack_bar("播放失败")
                    else:
                        self.show_snack_bar("裁剪音频失败")

                except Exception as e:
                    print(f"处理音频失败: {e}")
                    self.show_snack_bar(f"播放失败: {str(e)}")

            threading.Thread(target=process_and_play, daemon=True).start()

        except Exception as e:
            print(f"播放音频失败: {e}")
            self.show_snack_bar(f"播放失败: {str(e)}")

    def show_playback_progress(self, start_time, end_time):
        """显示播放进度"""
        duration = end_time - start_time
        if duration <= 0:
            return

        # 开始播放进度动画
        def update_progress():
            try:
                # 简单的进度显示
                self.show_snack_bar(f"播放中: {duration:.1f}秒")

                # 等待音频播放完成
                time.sleep(duration)

                # 播放完成
                self.show_snack_bar("播放完成")

            except Exception as e:
                print(f"更新进度失败: {e}")

        # 启动进度更新线程
        progress_thread = threading.Thread(target=update_progress, daemon=True)
        progress_thread.start()

    def stop_audio_playback(self, e=None):
        """停止音频播放"""
        try:
            audio_player.stop_audio()
            self.show_snack_bar("播放已停止")

        except Exception as e:
            print(f"停止播放失败: {e}")

    def clear_selection(self, e):
        """清除选择"""
        self.selection_start = None
        self.selection_end = None
        if hasattr(self, 'selection_rect'):
            self.selection_rect.opacity = 0
            self.selection_rect.update()

        if hasattr(self, 'selection_time_text'):
            self.selection_time_text.value = "选择区域: 未选择"
            self.selection_time_text.update()

        self.show_snack_bar("选择已清除")

    def update_selection_time_display(self):
        """更新选择时间显示"""
        if self.waveform_data is None or len(self.waveform_data) == 0 or self.audio_duration <= 0:
            return

        if self.selection_start is not None and self.selection_end is not None:
            track_width = self.audio_track_ref.width
            start_px = min(self.selection_start, self.selection_end)
            end_px = max(self.selection_start, self.selection_end)

            start_time = (start_px / track_width) * self.audio_duration
            end_time = (end_px / track_width) * self.audio_duration
            duration = end_time - start_time

            start_min = int(start_time // 60)
            start_sec = int(start_time % 60)
            end_min = int(end_time // 60)
            end_sec = int(end_time % 60)
            dur_min = int(duration // 60)
            dur_sec = int(duration % 60)

            time_text = f"选择: {start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d} ({dur_min:02d}:{dur_sec:02d})"
            self.selection_time_text.value = time_text
        else:
            self.selection_time_text.value = "选择区域: 未选择"

        if hasattr(self, 'selection_time_text'):
            self.selection_time_text.update()

    def start_playback_animation(self, duration):
        """开始播放动画"""

        def animate():
            # 在主线程中显示播放头
            if hasattr(self, 'progress_indicator'):
                self.progress_indicator.opacity = 1
                self.progress_indicator.update()

        self.page.add(ft.Container(width=0, height=0, on_click=lambda e: animate()))

    def update_playback_progress(self, progress, duration):
        """更新播放进度"""

        def update_ui():
            if not hasattr(self, 'progress_indicator') or not hasattr(self, 'waveform_canvas_ref'):
                return

            try:
                # 计算当前位置（像素）
                canvas_width = self.waveform_canvas_ref.width
                current_pos = progress * canvas_width

                # 更新进度指示器位置
                self.progress_indicator.left = current_pos

                # 更新时间显示
                if hasattr(self, 'timeline_text'):
                    current_time = progress * duration
                    minutes = int(current_time // 60)
                    seconds = int(current_time % 60)
                    total_minutes = int(duration // 60)
                    total_seconds = int(duration % 60)
                    time_text = f"{minutes:02d}:{seconds:02d} / {total_minutes:02d}:{total_seconds:02d}"
                    self.timeline_text.value = time_text

                # 更新UI
                if hasattr(self, 'progress_indicator'):
                    self.progress_indicator.update()
                if hasattr(self, 'timeline_text'):
                    self.timeline_text.update()

            except Exception as e:
                print(f"更新播放进度失败: {e}")

        # 在主线程中更新
        self.page.add(ft.Container(width=0, height=0, on_click=lambda e: update_ui()))

    def reset_playback_progress(self):
        """重置播放进度"""

        def reset_ui():
            if hasattr(self, 'progress_indicator'):
                self.progress_indicator.opacity = 0
                self.progress_indicator.left = 0
                self.progress_indicator.update()

            # 重置时间显示
            if hasattr(self, 'timeline_text') and hasattr(self, 'total_duration') and self.total_duration > 0:
                total_minutes = int(self.total_duration // 60)
                total_seconds = int(self.total_duration % 60)
                self.timeline_text.value = f"00:00 / {total_minutes:02d}:{total_seconds:02d}"
                self.timeline_text.update()

        self.page.add(ft.Container(width=0, height=0, on_click=lambda e: reset_ui()))

    def stop_audio_playback(self, e=None):
        """停止音频播放"""
        try:
            audio_player.stop_audio()
            self.playback_active = False
            self.reset_playback_progress()
            self.show_snack_bar("播放已停止")

        except Exception as e:
            print(f"停止播放失败: {e}")

    def cut_audio_segment(self, line):
        """剪切选中的音频区间 - 使用自定义模态弹窗"""
        print(f"=== cut_audio_segment 被调用 ===")

        if not hasattr(line, '_audio_track_info'):
            self.show_snack_bar("音频轨道信息不存在")
            return

        audio_info = line._audio_track_info

        # 检查是否有选中区间
        if (audio_info['selection_start'] is None or
                audio_info['selection_end'] is None or
                audio_info.get('total_duration', 0) <= 0):
            self.show_snack_bar("请先选择要剪切的区间")
            return

        # 获取选中时间
        track_width = audio_info.get('canvas_width', 340)
        start_px = min(audio_info['selection_start'], audio_info['selection_end'])
        end_px = max(audio_info['selection_start'], audio_info['selection_end'])

        start_time = (start_px / track_width) * audio_info['total_duration']
        end_time = (end_px / track_width) * audio_info['total_duration']

        print(f"选中区间: {start_time:.2f}s - {end_time:.2f}s")

        # ========== 创建自定义模态弹窗 ==========

        # 半透明背景层
        overlay_bg = ft.Container(
            width=self.page.width,
            height=self.page.height,
            bgcolor=ft.Colors.with_opacity(0.5, ft.Colors.BLACK),
            alignment=ft.alignment.center,
            on_click=lambda e: None  # 阻止点击穿透
        )

        # 弹窗内容
        dialog_content = ft.Container(
            width=400,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=20,
            content=ft.Column([
                ft.Text("剪切音频区间", size=20, weight=ft.FontWeight.BOLD),
                ft.Divider(height=1),
                ft.Text(f"音频文件: {os.path.basename(line.audio_path)}", size=14),
                ft.Text(f"开始时间: {start_time:.1f} 秒", size=14),
                ft.Text(f"结束时间: {end_time:.1f} 秒", size=14),
                ft.Text(f"剪切时长: {(end_time - start_time):.1f} 秒",
                        size=14, color=ft.Colors.RED_600),
                ft.Text("注意：此操作会永久删除该区间的音频内容。",
                        size=12, color=ft.Colors.ORANGE_600),
                ft.Row([
                    ft.ElevatedButton(
                        "取消",
                        on_click=lambda e: self._close_custom_dialog(),
                        style=ft.ButtonStyle(
                            color=ft.Colors.BLUE_GREY_700,
                            bgcolor=ft.Colors.GREY_200
                        )
                    ),
                    ft.ElevatedButton(
                        "剪切",
                        on_click=lambda e: self._execute_cut(line, start_time, end_time, audio_info),
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.RED_600
                        )
                    ),
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], spacing=10, tight=True)
        )

        # 将弹窗放在背景层之上
        dialog_stack = ft.Stack(
            [
                overlay_bg,
                ft.Container(
                    content=dialog_content,
                    alignment=ft.alignment.center
                )
            ],
            width=self.page.width,
            height=self.page.height
        )

        # 保存引用以便关闭
        self._custom_dialog_stack = dialog_stack

        # 添加到页面覆盖层
        self.page.overlay.append(dialog_stack)
        self.page.update()
        print("自定义弹窗已显示")

    def _close_custom_dialog(self):
        """关闭自定义弹窗"""
        if hasattr(self, '_custom_dialog_stack'):
            if self._custom_dialog_stack in self.page.overlay:
                self.page.overlay.remove(self._custom_dialog_stack)
            self.page.update()
            print("自定义弹窗已关闭")

    def _execute_cut(self, line, start_time, end_time, audio_info):
        """执行剪切操作"""
        print("执行剪切操作...")

        try:
            self._close_custom_dialog()
            self.show_snack_bar("正在剪切音频...")

            # 使用AudioProcessor剪切音频
            processor = AudioProcessor(line.audio_path)

            # 转换为毫秒
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)

            print(f"剪切音频: {line.audio_path}, 区间: {start_ms}ms - {end_ms}ms")

            # 执行剪切
            processor.cut(start_ms, end_ms)
            processor.cleanup()

            # 更新音频时长
            audio_info['total_duration'] = audio_info['total_duration'] - (end_time - start_time)

            # 清除选择状态
            self.clear_selection_for_line(line)

            # 重新加载波形
            if audio_info.get('canvas'):
                self._reload_waveform(line, audio_info['canvas'])

            self.show_snack_bar(f"已剪切区间: {start_time:.1f}s - {end_time:.1f}s")

        except Exception as ex:
            print(f"剪切音频失败: {ex}")
            import traceback
            traceback.print_exc()
            self.show_snack_bar(f"剪切失败: {str(ex)}")

    def _reload_waveform(self, line, canvas):
        """重新加载波形"""
        try:
            # 清除当前波形
            canvas.shapes = [
                cv.Rect(
                    0, 0, canvas.width, canvas.height,
                    paint=ft.Paint(color=ft.Colors.WHITE)
                )
            ]
            canvas.update()

            # 延迟后重新加载波形
            def delayed_reload():
                import time
                time.sleep(0.5)  # 给文件系统一点时间
                # 检查文件是否存在
                if hasattr(line, 'audio_path') and os.path.exists(line.audio_path):
                    self._load_and_draw_waveform_sync(line, canvas)
                else:
                    # 文件不存在，显示错误
                    canvas.shapes = [
                        cv.Text(
                            "音频文件丢失",
                            canvas.width / 2 - 30,
                            canvas.height / 2,
                            style=ft.TextStyle(color=ft.Colors.RED, size=12)
                        )
                    ]
                    canvas.update()

            threading.Thread(target=delayed_reload, daemon=True).start()

        except Exception as e:
            print(f"重新加载波形失败: {e}")




