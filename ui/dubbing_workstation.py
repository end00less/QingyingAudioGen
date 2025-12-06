# ui/dubbing_workstation.py
import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Optional, List, Dict, Any
import threading


class DubbingWorkstation:
    def __init__(self, parent, app_controller, project):
        self.app_controller = app_controller
        self.project = project
        self.current_chapter = None
        self.dialog_lines = []

        # 创建工作台窗口
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"配音工作台 - {project.name}")
        self.window.geometry("1400x900")
        self.window.transient(parent)

        self.setup_ui()
        self.load_chapters()

    def setup_ui(self):
        """设置主界面布局"""
        # 主容器
        self.main_container = ctk.CTkFrame(self.window)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # 创建各个区域
        self.create_header()
        self.create_chapter_section()
        self.create_content_section()
        self.create_dialogue_section()

    def create_header(self):
        """创建顶部导航栏"""
        header_frame = ctk.CTkFrame(self.main_container)
        header_frame.pack(fill="x", pady=(0, 10))

        # 左侧标题
        title_label = ctk.CTkLabel(
            header_frame,
            text="🎤 开始配音",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=15)

        # 右侧返回按钮
        back_btn = ctk.CTkButton(
            header_frame,
            text="🔙 返回",
            command=self.window.destroy,
            height=40,
            width=100,
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        back_btn.pack(side="right", padx=20, pady=15)

    def create_chapter_section(self):
        """创建章节管理区"""
        chapter_frame = ctk.CTkFrame(self.main_container)
        chapter_frame.pack(fill="x", pady=(0, 10))

        # 顶部控制栏
        control_bar = ctk.CTkFrame(chapter_frame)
        control_bar.pack(fill="x", padx=15, pady=10)

        # 左侧标签
        ctk.CTkLabel(
            control_bar,
            text="📚 配音目录",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", pady=10)

        # 右侧操作按钮
        btn_frame = ctk.CTkFrame(control_bar)
        btn_frame.pack(side="right")

        # 项目设置按钮
        settings_btn = ctk.CTkButton(
            btn_frame,
            text="⚙️ 项目设置",
            command=self.open_project_settings,
            height=35,
            width=100,
            fg_color="#27ae60",
            hover_color="#229954"
        )
        settings_btn.pack(side="left", padx=5)

        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 刷新",
            command=self.refresh_chapters,
            height=35,
            width=80
        )
        refresh_btn.pack(side="left", padx=5)

        # 创建章节按钮
        create_chapter_btn = ctk.CTkButton(
            btn_frame,
            text="➕ 创建章节",
            command=self.create_chapter,
            height=35,
            width=100,
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        create_chapter_btn.pack(side="left", padx=5)

        # 章节按钮容器
        self.chapter_buttons_frame = ctk.CTkFrame(chapter_frame)
        self.chapter_buttons_frame.pack(fill="x", padx=15, pady=(0, 10))

    def create_content_section(self):
        """创建内容编辑区"""
        content_frame = ctk.CTkFrame(self.main_container)
        content_frame.pack(fill="x", pady=(0, 10))

        # 标题
        ctk.CTkLabel(
            content_frame,
            text="📝 章节内容",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))

        # 内容编辑区域
        self.content_text = ctk.CTkTextbox(
            content_frame,
            height=150,
            font=ctk.CTkFont(size=14)
        )
        self.content_text.pack(fill="x", padx=15, pady=(0, 10))

        # 提示文本
        self.content_text.insert("0.0", "还没有章节内容，去创建一个吧")

    def create_dialogue_section(self):
        """创建台词配置区"""
        dialogue_frame = ctk.CTkFrame(self.main_container)
        dialogue_frame.pack(fill="both", expand=True)

        # 标签切换栏
        tab_frame = ctk.CTkFrame(dialogue_frame)
        tab_frame.pack(fill="x", padx=15, pady=10)

        # 台词管理标签（激活）
        self.dialogue_tab = ctk.CTkButton(
            tab_frame,
            text="台词管理",
            command=lambda: self.switch_tab("dialogue"),
            height=40,
            width=120,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        self.dialogue_tab.pack(side="left", padx=(0, 5))

        # 角色标签（未激活）
        self.roles_tab = ctk.CTkButton(
            tab_frame,
            text="本章节角色",
            command=lambda: self.switch_tab("roles"),
            height=40,
            width=120,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30")
        )
        self.roles_tab.pack(side="left")

        # 台词表格容器
        self.dialogue_container = ctk.CTkFrame(dialogue_frame)
        self.dialogue_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # 创建台词表格
        self.create_dialogue_table()

    def create_dialogue_table(self):
        """创建台词管理表格"""
        # 表格头部
        header_frame = ctk.CTkFrame(self.dialogue_container)
        header_frame.pack(fill="x", pady=(0, 5))

        headers = ["编号", "文案", "角色", "情绪", "强度", "试听设置", "操作"]
        header_widths = [60, 300, 120, 100, 100, 250, 200]

        for i, (header, width) in enumerate(zip(headers, header_widths)):
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=width
            ).pack(side="left", padx=2, pady=5)

        # 台词行容器（可滚动）
        self.dialogue_scroll = ctk.CTkScrollableFrame(
            self.dialogue_container,
            height=400
        )
        self.dialogue_scroll.pack(fill="both", expand=True)

        # 添加初始台词行
        self.add_dialogue_row()

    def add_dialogue_row(self, dialogue_data=None):
        """添加台词行"""
        row_frame = ctk.CTkFrame(self.dialogue_scroll)
        row_frame.pack(fill="x", pady=2)

        # 编号
        row_num = len(self.dialogue_lines) + 1
        num_label = ctk.CTkLabel(
            row_frame,
            text=str(row_num),
            width=60
        )
        num_label.pack(side="left", padx=2, pady=2)

        # 文案输入框
        text_entry = ctk.CTkEntry(
            row_frame,
            width=300,
            placeholder_text="输入台词内容..."
        )
        text_entry.pack(side="left", padx=2, pady=2)
        if dialogue_data and 'text' in dialogue_data:
            text_entry.insert(0, dialogue_data['text'])

        # 角色选择
        role_combo = ctk.CTkComboBox(
            row_frame,
            width=120,
            values=["请选择", "主角", "配角", "旁白"]
        )
        role_combo.pack(side="left", padx=2, pady=2)
        role_combo.set("请选择")

        # 情绪选择
        emotion_combo = ctk.CTkComboBox(
            row_frame,
            width=100,
            values=["请选择", "开心", "悲伤", "愤怒", "平静"]
        )
        emotion_combo.pack(side="left", padx=2, pady=2)
        emotion_combo.set("请选择")

        # 强度选择
        intensity_combo = ctk.CTkComboBox(
            row_frame,
            width=100,
            values=["请选择", "正常", "强调", "轻声"]
        )
        intensity_combo.pack(side="left", padx=2, pady=2)
        intensity_combo.set("请选择")

        # 试听设置
        audio_settings_frame = ctk.CTkFrame(row_frame)
        audio_settings_frame.pack(side="left", padx=2, pady=2)

        # 速度滑块
        speed_label = ctk.CTkLabel(audio_settings_frame, text="速度:")
        speed_label.pack(anchor="w")
        speed_slider = ctk.CTkSlider(
            audio_settings_frame,
            from_=0.5,
            to=2.0,
            width=200
        )
        speed_slider.set(1.0)
        speed_slider.pack(fill="x")

        # 音量滑块
        volume_label = ctk.CTkLabel(audio_settings_frame, text="音量:")
        volume_label.pack(anchor="w")
        volume_slider = ctk.CTkSlider(
            audio_settings_frame,
            from_=0.0,
            to=1.0,
            width=200
        )
        volume_slider.set(0.8)
        volume_slider.pack(fill="x")

        # 操作按钮
        action_frame = ctk.CTkFrame(row_frame)
        action_frame.pack(side="left", padx=2, pady=2)

        # 生成音频按钮
        generate_btn = ctk.CTkButton(
            action_frame,
            text="🎵 生成",
            command=lambda: self.generate_audio(row_num),
            height=30,
            width=60,
            fg_color="#3498db",
            hover_color="#2980b9"
        )
        generate_btn.pack(pady=1)

        # 试听按钮
        play_btn = ctk.CTkButton(
            action_frame,
            text="▶️ 试听",
            command=lambda: self.play_audio(row_num),
            height=30,
            width=60,
            fg_color="#27ae60",
            hover_color="#229954"
        )
        play_btn.pack(pady=1)

        # 删除按钮
        delete_btn = ctk.CTkButton(
            action_frame,
            text="🗑️ 删除",
            command=lambda: self.delete_dialogue_row(row_frame),
            height=30,
            width=60,
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        delete_btn.pack(pady=1)

        # 插入行按钮
        insert_btn = ctk.CTkButton(
            action_frame,
            text="➕ 插入",
            command=lambda: self.insert_dialogue_row(row_frame),
            height=30,
            width=60,
            fg_color="#f39c12",
            hover_color="#e67e22"
        )
        insert_btn.pack(pady=1)

        # 保存行数据
        dialogue_row = {
            'frame': row_frame,
            'text': text_entry,
            'role': role_combo,
            'emotion': emotion_combo,
            'intensity': intensity_combo,
            'speed': speed_slider,
            'volume': volume_slider
        }
        self.dialogue_lines.append(dialogue_row)

    def insert_dialogue_row(self, above_frame):
        """在指定行上方插入新行"""
        # 找到插入位置
        insert_index = 0
        for i, line in enumerate(self.dialogue_lines):
            if line['frame'] == above_frame:
                insert_index = i
                break

        # 插入新行
        self.add_dialogue_row()

        # 重新排序编号
        self.reorder_dialogue_numbers()

    def delete_dialogue_row(self, frame):
        """删除台词行"""
        # 找到要删除的行
        for i, line in enumerate(self.dialogue_lines):
            if line['frame'] == frame:
                # 删除界面元素
                frame.destroy()
                # 从列表中移除
                self.dialogue_lines.pop(i)
                break

        # 重新排序编号
        self.reorder_dialogue_numbers()

    def reorder_dialogue_numbers(self):
        """重新排序台词编号"""
        for i, line in enumerate(self.dialogue_lines):
            # 更新编号标签
            for widget in line['frame'].winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("text").isdigit():
                    widget.configure(text=str(i + 1))
                    break

    def switch_tab(self, tab_name):
        """切换标签页"""
        if tab_name == "dialogue":
            self.dialogue_tab.configure(
                fg_color="#e74c3c",
                text_color="white"
            )
            self.roles_tab.configure(
                fg_color="transparent",
                text_color=("gray10", "gray90")
            )
        else:
            self.roles_tab.configure(
                fg_color="#e74c3c",
                text_color="white"
            )
            self.dialogue_tab.configure(
                fg_color="transparent",
                text_color=("gray10", "gray90")
            )
            messagebox.showinfo("提示", "角色管理功能开发中...")

    def load_chapters(self):
        """加载章节数据"""
        # 创建示例章节按钮
        chapters = ["第一集", "第二集", "第三集", "第四集", "第五集", "第六集"]
        colors = ["#9b59b6", "#e74c3c", "#f39c12", "#9b59b6", "#e74c3c", "#f39c12"]

        for i, (chapter, color) in enumerate(zip(chapters, colors)):
            btn = ctk.CTkButton(
                self.chapter_buttons_frame,
                text=chapter,
                command=lambda c=chapter: self.select_chapter(c),
                height=40,
                width=100,
                fg_color=color,
                hover_color=self.darken_color(color)
            )
            btn.pack(side="left", padx=5, pady=5)

    def select_chapter(self, chapter_name):
        """选择章节"""
        self.current_chapter = chapter_name
        messagebox.showinfo("章节选择", f"已选择：{chapter_name}")
        # 这里可以加载章节的具体内容

    def create_chapter(self):
        """创建新章节"""
        messagebox.showinfo("提示", "创建章节功能开发中...")

    def refresh_chapters(self):
        """刷新章节列表"""
        messagebox.showinfo("提示", "章节列表已刷新")

    def open_project_settings(self):
        """打开项目设置"""
        messagebox.showinfo("提示", "项目设置功能开发中...")

    def generate_audio(self, row_num):
        """生成音频"""

        # 在后台线程中生成音频
        def generate():
            messagebox.showinfo("生成音频", f"正在生成第{row_num}行音频...")

        threading.Thread(target=generate, daemon=True).start()

    def play_audio(self, row_num):
        """试听音频"""
        messagebox.showinfo("试听", f"播放第{row_num}行音频")

    def darken_color(self, color):
        """使颜色变暗（用于hover效果）"""
        # 简单的颜色变暗处理
        color_map = {
            "#9b59b6": "#8e44ad",
            "#e74c3c": "#c0392b",
            "#f39c12": "#e67e22"
        }
        return color_map.get(color, color)
