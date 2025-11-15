# ui/chapter_window.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
from app.core.app_context import AppContext
from app.controllers.base_controller import BusinessException

class ChapterWindow:
    def __init__(self, parent, project, app_controller):
        self.parent = parent
        self.project = project
        self.app_controller = app_controller
        self.chapter_controller = app_controller.chapter_controller

        self.setup_window()
        self.load_chapters()

    def setup_window(self):
        """设置章节管理窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(f"章节管理 - {self.project.name}")
        self.window.geometry("900x700")
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 章节列表框架
        list_frame = ttk.LabelFrame(main_frame, text="章节列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 章节树形视图
        columns = ('id', 'title', 'order_index', 'created_at')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        # 设置列
        self.tree.heading('id', text='ID')
        self.tree.heading('title', text='章节标题')
        self.tree.heading('order_index', text='排序')
        self.tree.heading('created_at', text='创建时间')

        self.tree.column('id', width=50)
        self.tree.column('title', width=200)
        self.tree.column('order_index', width=60)
        self.tree.column('created_at', width=120)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<<TreeviewSelect>>', self.on_chapter_select)

        # 章节操作按钮
        chapter_btn_frame = ttk.Frame(main_frame)
        chapter_btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(chapter_btn_frame, text="添加章节", command=self.add_chapter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(chapter_btn_frame, text="编辑章节", command=self.edit_chapter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(chapter_btn_frame, text="删除章节", command=self.delete_chapter).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(chapter_btn_frame, text="导入文本", command=self.import_text).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(chapter_btn_frame, text="刷新", command=self.load_chapters).pack(side=tk.LEFT)

        # 章节内容框架
        content_frame = ttk.LabelFrame(main_frame, text="章节内容", padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 内容编辑区域
        self.content_text = scrolledtext.ScrolledText(content_frame, height=15, wrap=tk.WORD)
        self.content_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 内容操作按钮
        content_btn_frame = ttk.Frame(content_frame)
        content_btn_frame.pack(fill=tk.X)

        ttk.Button(content_btn_frame, text="保存内容", command=self.save_content).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(content_btn_frame, text="解析台词", command=self.parse_lines).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(content_btn_frame, text="管理台词", command=self.manage_lines).pack(side=tk.LEFT)

    def load_chapters(self):
        """通过 Controller 加载章节"""
        try:
            chapters = self.chapter_controller.get_chapters_by_project(self.project.id)

            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)

            for chapter in chapters:
                self.tree.insert('', tk.END, values=(
                    chapter.id,
                    chapter.title,
                    chapter.order_index or '',
                    chapter.created_at[:19] if chapter.created_at else ''
                ))
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def add_chapter(self):
        """通过 Controller 添加章节"""
        try:
            dialog = ChapterEditDialog(self.window, self.chapter_controller, self.project.id)
            if dialog.result:
                self.load_chapters()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def edit_chapter(self):
        """通过 Controller 编辑章节"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个章节")
            return

        item = self.tree.item(selection[0])
        chapter_id = item['values'][0]

        try:
            chapter = self.chapter_controller.get_chapter(chapter_id)
            if chapter:
                dialog = ChapterEditDialog(self.window, self.chapter_controller, self.project.id, chapter)
                if dialog.result:
                    self.load_chapters()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def delete_chapter(self):
        """通过 Controller 删除章节"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个章节")
            return

        item = self.tree.item(selection[0])
        chapter_id = item['values'][0]
        chapter_title = item['values'][1]

        try:
            if messagebox.askyesno("确认删除", f"确定要删除章节 '{chapter_title}' 吗？"):
                self.chapter_controller.delete_chapter(chapter_id)
                messagebox.showinfo("成功", "章节删除成功")
                self.load_chapters()
                self.content_text.delete(1.0, tk.END)
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def save_content(self):
        """通过 Controller 保存章节内容"""
        if not hasattr(self, 'current_chapter_id'):
            messagebox.showwarning("警告", "请先选择一个章节")
            return

        content = self.content_text.get(1.0, tk.END).strip()
        try:
            self.chapter_controller.update_chapter(self.current_chapter_id, text_content=content)
            messagebox.showinfo("成功", "内容保存成功")
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def parse_lines(self):
        """通过 Controller 解析台词"""
        if not hasattr(self, 'current_chapter_id'):
            messagebox.showwarning("警告", "请先选择一个章节")
            return

        try:
            from ui.line_parse_dialog import LineParseDialog
            dialog = LineParseDialog(
                self.window, self.current_chapter_id, self.project, self.app_controller
            )
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def manage_lines(self):
        """通过 Controller 管理台词"""
        if not hasattr(self, 'current_chapter_id'):
            messagebox.showwarning("警告", "请先选择一个章节")
            return

        try:
            from ui.line_window import LineWindow
            line_window = LineWindow(self.window, self.current_chapter_id, self.project, self.app_controller)
        except BusinessException as e:
            messagebox.showerror("错误", e.message)