# ui/line_window.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import os
import threading
from app.core.app_context import AppContext
from app.controllers.base_controller import BusinessException

class LineWindow:
    def __init__(self, parent, chapter_id, project, app_controller):
        self.parent = parent
        self.chapter_id = chapter_id
        self.project = project
        self.app_controller = app_controller
        self.line_controller = app_controller.line_controller
        self.role_controller = app_controller.role_controller

        self.setup_window()
        self.load_lines()
        self.load_roles()

    def setup_window(self):
        """设置台词管理窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("台词管理")
        self.window.geometry("1000x700")

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 台词列表框架
        list_frame = ttk.LabelFrame(main_frame, text="台词列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 台词树形视图
        columns = ('id', 'order', 'role', 'text', 'emotion', 'strength', 'status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        # 设置列
        self.tree.heading('id', text='ID')
        self.tree.heading('order', text='序号')
        self.tree.heading('role', text='角色')
        self.tree.heading('text', text='台词内容')
        self.tree.heading('emotion', text='情绪')
        self.tree.heading('strength', text='强度')
        self.tree.heading('status', text='状态')

        self.tree.column('id', width=50)
        self.tree.column('order', width=50)
        self.tree.column('role', width=80)
        self.tree.column('text', width=300)
        self.tree.column('emotion', width=60)
        self.tree.column('strength', width=60)
        self.tree.column('status', width=80)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<<TreeviewSelect>>', self.on_line_select)

        # 台词操作按钮
        line_btn_frame = ttk.Frame(main_frame)
        line_btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(line_btn_frame, text="添加台词", command=self.add_line).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(line_btn_frame, text="编辑台词", command=self.edit_line).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(line_btn_frame, text="删除台词", command=self.delete_line).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(line_btn_frame, text="生成语音", command=self.generate_audio).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(line_btn_frame, text="批量生成", command=self.batch_generate).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(line_btn_frame, text="导出项目", command=self.export_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(line_btn_frame, text="刷新", command=self.load_lines).pack(side=tk.LEFT)

        # 台词编辑框架
        edit_frame = ttk.LabelFrame(main_frame, text="台词编辑", padding="10")
        edit_frame.pack(fill=tk.BOTH, expand=True)

        # 编辑表单
        form_frame = ttk.Frame(edit_frame)
        form_frame.pack(fill=tk.X, pady=(0, 10))

        # 角色选择
        ttk.Label(form_frame, text="角色:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(form_frame, textvariable=self.role_var, width=20)
        self.role_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 20))

        # 音色选择
        ttk.Label(form_frame, text="音色:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(form_frame, textvariable=self.voice_var, width=20)
        self.voice_combo.grid(row=0, column=3, sticky=tk.W, pady=5, padx=(5, 0))

        # 情绪选择
        ttk.Label(form_frame, text="情绪:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.emotion_var = tk.StringVar()
        self.emotion_combo = ttk.Combobox(form_frame, textvariable=self.emotion_var, width=20)
        self.emotion_combo['values'] = ('高兴', '生气', '伤心', '害怕', '厌恶', '低落', '惊喜', '平静')
        self.emotion_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 20))

        # 强度选择
        ttk.Label(form_frame, text="强度:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.strength_var = tk.StringVar()
        self.strength_combo = ttk.Combobox(form_frame, textvariable=self.strength_var, width=20)
        self.strength_combo['values'] = ('微弱', '稍弱', '中等', '较强', '强烈')
        self.strength_combo.grid(row=1, column=3, sticky=tk.W, pady=5, padx=(5, 0))

        # 台词内容
        ttk.Label(edit_frame, text="台词内容:").pack(anchor=tk.W, pady=(0, 5))
        self.line_text = scrolledtext.ScrolledText(edit_frame, height=6, wrap=tk.WORD)
        self.line_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 编辑操作按钮
        edit_btn_frame = ttk.Frame(edit_frame)
        edit_btn_frame.pack(fill=tk.X)

        ttk.Button(edit_btn_frame, text="保存台词", command=self.save_line).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(edit_btn_frame, text="播放音频", command=self.play_audio).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(edit_btn_frame, text="编辑音频", command=self.edit_audio).pack(side=tk.LEFT)

    def load_lines(self):
        """通过 Controller 加载台词"""
        try:
            lines = self.line_controller.get_lines_by_chapter(self.chapter_id)

            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)

            for line in lines:
                role_name = self.get_role_name(line.role_id)
                self.tree.insert('', tk.END, values=(
                    line.id,
                    line.line_order or '',
                    role_name,
                    line.text_content[:50] + "..." if len(line.text_content) > 50 else line.text_content,
                    self.get_emotion_name(line.emotion_id),
                    self.get_strength_name(line.strength_id),
                    line.status or 'pending'
                ))
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def load_roles(self):
        """通过 Controller 加载角色"""
        try:
            roles = self.role_controller.get_roles_by_project(self.project.id)
            role_names = [role.name for role in roles]
            self.role_combo['values'] = role_names
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def save_line(self):
        """通过 Controller 保存台词"""
        text_content = self.line_text.get(1.0, tk.END).strip()
        if not text_content:
            messagebox.showwarning("警告", "请输入台词内容")
            return

        role_name = self.role_var.get().strip()
        if not role_name:
            messagebox.showwarning("警告", "请选择角色")
            return

        try:
            # 获取或创建角色
            roles = self.role_controller.get_roles_by_project(self.project.id)
            role = next((r for r in roles if r.name == role_name), None)

            if not role:
                role = self.role_controller.create_role(self.project.id, role_name)

            if hasattr(self, 'current_line_id'):
                # 更新台词
                update_data = {
                    'role_id': role.id,
                    'text_content': text_content,
                    'emotion_id': self.get_emotion_id(self.emotion_var.get()),
                    'strength_id': self.get_strength_id(self.strength_var.get())
                }
                self.line_controller.update_line(self.current_line_id, **update_data)
                messagebox.showinfo("成功", "台词更新成功")
                self.load_lines()
            else:
                # 新建台词
                self.line_controller.create_line(
                    chapter_id=self.chapter_id,
                    text_content=text_content,
                    role_id=role.id,
                    emotion_id=self.get_emotion_id(self.emotion_var.get()),
                    strength_id=self.get_strength_id(self.strength_var.get())
                )
                messagebox.showinfo("成功", "台词创建成功")
                self.load_lines()
                self.add_line()  # 清空为下一次输入准备

        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def delete_line(self):
        """通过 Controller 删除台词"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个台词")
            return

        item = self.tree.item(selection[0])
        line_id = item['values'][0]

        try:
            if messagebox.askyesno("确认删除", "确定要删除这个台词吗？"):
                self.line_controller.delete_line(line_id)
                messagebox.showinfo("成功", "台词删除成功")
                self.load_lines()
                self.add_line()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)