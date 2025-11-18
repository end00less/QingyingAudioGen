# ui/chapter_editor.py - 修复布局版本
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
import threading
from app.core.app_context import AppContext
from app.controllers.base_controller import BusinessException


class ChapterEditor(ttk.Frame):
    def __init__(self, parent, project, app_controller):
        super().__init__(parent)  # 调用父类初始化

        self.parent = parent
        self.project = project
        self.app_controller = app_controller
        self.chapter_controller = app_controller.chapter_controller
        self.line_controller = app_controller.line_controller
        self.role_controller = app_controller.role_controller
        self.current_chapter_id = None
        self.current_line_id = None

        # 添加padding到整个Frame
        self.pack_propagate(False)  # 防止子组件改变父组件大小

        self.setup_ui()
        self.load_chapters()

    def setup_ui(self):
        """设置UI界面"""
        # 创建主容器，添加padding
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # 左右分栏布局
        paned_window = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # 左侧章节列表（窄一点）
        left_frame = ttk.Frame(paned_window, width=250)
        paned_window.add(left_frame, weight=1)

        # 右侧内容区域
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=3)

        self.setup_chapter_list(left_frame)
        self.setup_content_area(right_frame)

    def setup_chapter_list(self, parent):
        """设置章节列表（窄版）"""
        # 章节列表框架
        list_frame = ttk.LabelFrame(parent, text="章节列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # 工具栏（只有3个按钮）
        toolbar_frame = ttk.Frame(list_frame)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar_frame, text="添加", command=self.add_chapter, width=8).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="编辑", command=self.edit_chapter, width=8).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="删除", command=self.delete_chapter, width=8).pack(side=tk.LEFT)

        # 章节树形视图（保留ID列但不显示）
        columns = ('id', 'title', 'lines_count')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=20)

        # 设置列标题（只显示标题和台词数）
        self.tree.heading('title', text='章节标题')
        self.tree.heading('lines_count', text='台词数')

        # 设置列宽（隐藏ID列）
        self.tree.column('id', width=0, stretch=False)  # 宽度为0，不拉伸
        self.tree.column('title', width=180)
        self.tree.column('lines_count', width=60)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<<TreeviewSelect>>', self.on_chapter_select)
        self.tree.bind('<Double-1>', self.on_chapter_double_click)

    def setup_content_area(self, parent):
        """设置右侧内容区域"""
        # 上下分栏
        content_paned = ttk.PanedWindow(parent, orient=tk.VERTICAL)
        content_paned.pack(fill=tk.BOTH, expand=True)

        # 上半部分：章节内容
        chapter_frame = ttk.LabelFrame(content_paned, text="章节内容", padding="10")
        content_paned.add(chapter_frame, weight=1)

        # 下半部分：台词管理
        lines_frame = ttk.LabelFrame(content_paned, text="台词管理", padding="10")
        content_paned.add(lines_frame, weight=8)

        self.setup_chapter_content(chapter_frame)
        self.setup_lines_management(lines_frame)

    def setup_chapter_content(self, parent):
        """设置章节内容区域（简化版）"""
        # 工具栏
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar_frame, text="从文本导入", command=self.import_text_with_parsing).pack(side=tk.LEFT)

        # 状态标签
        self.chapter_status_var = tk.StringVar(value="请选择章节")
        ttk.Label(toolbar_frame, textvariable=self.chapter_status_var).pack(side=tk.RIGHT)

    def setup_lines_management(self, parent):
        """设置台词管理区域"""
        # 左右分栏
        lines_paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        lines_paned.pack(fill=tk.BOTH, expand=True)

        # 左侧：台词列表
        lines_list_frame = ttk.Frame(lines_paned)
        lines_paned.add(lines_list_frame, weight=2)

        # 右侧：台词编辑
        lines_edit_frame = ttk.Frame(lines_paned)
        lines_paned.add(lines_edit_frame, weight=1)

        self.setup_lines_list(lines_list_frame)
        self.setup_line_editor(lines_edit_frame)

    def setup_lines_list(self, parent):
        """设置台词列表"""
        # 工具栏
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar_frame, text="添加台词", command=self.add_line, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="删除台词", command=self.delete_line, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="生成语音", command=self.generate_audio, width=10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar_frame, text="批量生成", command=self.batch_generate, width=10).pack(side=tk.LEFT)

        # 台词列表
        columns = ('id', 'order', 'role', 'text_preview', 'status')
        self.lines_tree = ttk.Treeview(parent, columns=columns, show='headings')

        # 设置列标题
        self.lines_tree.heading('id', text='ID')
        self.lines_tree.heading('order', text='序号')
        self.lines_tree.heading('role', text='角色')
        self.lines_tree.heading('text_preview', text='台词内容')
        self.lines_tree.heading('status', text='状态')

        # 设置列宽
        self.lines_tree.column('id', width=40)
        self.lines_tree.column('order', width=40)
        self.lines_tree.column('role', width=80)
        self.lines_tree.column('text_preview', width=200)
        self.lines_tree.column('status', width=60)

        # 滚动条
        lines_scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.lines_tree.yview)
        self.lines_tree.configure(yscrollcommand=lines_scrollbar.set)

        self.lines_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        lines_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.lines_tree.bind('<<TreeviewSelect>>', self.on_line_select)

    def setup_line_editor(self, parent):
        """设置台词编辑器"""
        # 编辑表单
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=tk.X, pady=(0, 10))

        # 角色选择
        ttk.Label(form_frame, text="角色:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(form_frame, textvariable=self.role_var, width=15)
        self.role_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 10))

        # 情绪选择
        ttk.Label(form_frame, text="情绪:").grid(row=0, column=2, sticky=tk.W, pady=5)
        self.emotion_var = tk.StringVar()
        self.emotion_combo = ttk.Combobox(form_frame, textvariable=self.emotion_var, width=15)
        self.emotion_combo['values'] = ('高兴', '生气', '伤心', '害怕', '厌恶', '低落', '惊喜', '平静')
        self.emotion_combo.grid(row=0, column=3, sticky=tk.W, pady=5, padx=(5, 0))

        # 强度选择
        ttk.Label(form_frame, text="强度:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.strength_var = tk.StringVar()
        self.strength_combo = ttk.Combobox(form_frame, textvariable=self.strength_var, width=15)
        self.strength_combo['values'] = ('微弱', '稍弱', '中等', '较强', '强烈')
        self.strength_combo.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(5, 10))

        # 台词内容
        ttk.Label(form_frame, text="台词内容:").grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=5)
        self.line_text = scrolledtext.ScrolledText(form_frame, height=8, wrap=tk.WORD, font=("Microsoft YaHei", 9))
        self.line_text.grid(row=3, column=0, columnspan=4, sticky=tk.W + tk.E, pady=5)

        # 操作按钮
        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=10)

        ttk.Button(btn_frame, text="保存台词", command=self.save_line, width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="播放音频", command=self.play_audio, width=12).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="编辑音频", command=self.edit_audio, width=12).pack(side=tk.LEFT)

        # 配置权重
        form_frame.columnconfigure(3, weight=1)

    # 以下方法保持不变...
    def load_chapters(self):
        """加载章节列表"""
        try:
            chapters = self.chapter_controller.get_chapters_by_project(self.project.id)

            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)

            for chapter in chapters:
                # 获取台词数量
                try:
                    lines = self.line_controller.get_lines_by_chapter(chapter.id)
                    lines_count = len(lines)
                except:
                    lines_count = 0

                self.tree.insert('', tk.END, values=(
                    chapter.id,
                    chapter.title,
                    lines_count
                ))
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def on_chapter_select(self, event):
        """章节选择事件"""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        chapter_id = item['values'][0]
        chapter_title = item['values'][1]

        self.current_chapter_id = chapter_id
        self.chapter_status_var.set(f"当前章节: {chapter_title}")

        try:
            # 加载台词列表
            self.load_lines()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def on_chapter_double_click(self, event):
        """章节双击事件"""
        selection = self.tree.selection()
        if not selection:
            return

        # 双击章节时，焦点移到台词编辑区域
        self.add_line()

    def load_lines(self):
        """加载台词列表"""
        if not self.current_chapter_id:
            return

        try:
            lines = self.line_controller.get_lines_by_chapter(self.current_chapter_id)

            # 清空现有数据
            for item in self.lines_tree.get_children():
                self.lines_tree.delete(item)

            for line in lines:
                role_name = self.get_role_name(line.role_id)
                self.lines_tree.insert('', tk.END, values=(
                    line.id,
                    line.line_order or '',
                    role_name,
                    line.text_content[:30] + "..." if len(line.text_content) > 30 else line.text_content,
                    line.status or 'pending'
                ))
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def on_line_select(self, event):
        """台词选择事件"""
        selection = self.lines_tree.selection()
        if not selection:
            return

        item = self.lines_tree.item(selection[0])
        line_id = item['values'][0]

        try:
            line = self.line_controller.get_line(line_id)
            if line:
                self.current_line_id = line_id
                self.line_text.delete(1.0, tk.END)
                self.line_text.insert(1.0, line.text_content or '')

                # 设置角色
                role_name = self.get_role_name(line.role_id)
                self.role_var.set(role_name)

                # 设置情绪和强度
                self.emotion_var.set(self.get_emotion_name(line.emotion_id))
                self.strength_var.set(self.get_strength_name(line.strength_id))
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def add_chapter(self):
        """添加章节"""
        try:
            from app.ui.chapter_edit_dialog import ChapterEditDialog
            dialog = ChapterEditDialog(self, self.chapter_controller, self.project.id)

            # 等待对话框关闭
            self.wait_window(dialog.dialog)

            # print("对话框结果:", dialog.result)  # 调试
            if dialog.result:
                # print("章节创建成功，刷新列表")
                self.load_chapters()
            else:
                print("章节创建失败或用户取消")
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def edit_chapter(self):
        """编辑章节"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个章节")
            return

        item = self.tree.item(selection[0])
        chapter_id = item['values'][0]

        try:
            chapter = self.chapter_controller.get_chapter(chapter_id)
            if chapter:
                from app.ui.chapter_edit_dialog import ChapterEditDialog
                dialog = ChapterEditDialog(self, self.chapter_controller, self.project.id, chapter)
                if dialog.result:
                    self.load_chapters()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def delete_chapter(self):
        """删除章节"""
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
                self.clear_content()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def import_text_with_parsing(self):
        """导入文本并自动解析台词"""
        if not self.current_chapter_id:
            messagebox.showwarning("警告", "请先选择一个章节")
            return

        file_path = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 检查项目是否配置了LLM
                if not self.project.llm_provider_id or not self.project.llm_model:
                    messagebox.showerror("错误", "项目未配置LLM服务商，请先在项目设置中配置")
                    return

                # 确认对话框
                if not messagebox.askyesno("确认", f"确定要导入文本并自动解析台词吗？\n文件大小: {len(content)} 字符\n这可能需要一些时间。"):
                    return

                # 创建进度对话框
                progress_window = tk.Toplevel(self)
                progress_window.title("导入并解析")
                progress_window.geometry("450x180")
                progress_window.transient(self)
                progress_window.grab_set()
                progress_window.resizable(False, False)

                # 防止用户关闭进度窗口
                progress_window.protocol("WM_DELETE_WINDOW", lambda: None)

                progress_frame = ttk.Frame(progress_window, padding="20")
                progress_frame.pack(fill=tk.BOTH, expand=True)

                ttk.Label(progress_frame, text="正在导入文本并解析台词，请稍候...",
                          font=("Arial", 10, "bold")).pack(pady=(0, 10))

                # 进度状态标签
                progress_status = ttk.Label(progress_frame, text="准备中...")
                progress_status.pack(pady=5)

                # 进度条（确定模式）
                progress_var = tk.DoubleVar()
                progress_bar = ttk.Progressbar(progress_frame, variable=progress_var,
                                               maximum=100, mode='determinate')
                progress_bar.pack(fill=tk.X, pady=10)

                # 进度百分比标签
                progress_percent = ttk.Label(progress_frame, text="0%")
                progress_percent.pack()

                # 在新线程中执行导入和解析
                def run_import_and_parse():
                    try:
                        # 定义进度回调函数
                        def on_progress(current, total, message):
                            # 计算百分比
                            percent = int((current / total) * 100) if total > 0 else 0
                            # 在主线程中更新UI
                            self.after(0, lambda: update_progress_ui(current, total, percent, message))

                        # UI更新函数
                        def update_progress_ui(current, total, percent, message):
                            progress_status.config(text=message)
                            progress_var.set(percent)
                            progress_percent.config(text=f"{percent}%")
                            progress_window.update()

                        # 初始进度
                        self.after(0, lambda: update_progress_ui(0, 1, 0, "正在更新章节内容..."))

                        # 修复：正确调用 update_chapter 方法
                        # 先获取当前章节信息
                        current_chapter = self.chapter_controller.get_chapter(self.current_chapter_id)
                        if not current_chapter:
                            raise BusinessException("章节不存在")

                        # 构建更新数据字典
                        update_data = {
                            "title": current_chapter.title,  # 保持原有标题
                            "project_id": current_chapter.project_id,  # 保持原有项目ID
                            "text_content": content  # 更新文本内容
                        }

                        # 更新章节内容
                        success = self.chapter_controller.update_chapter(self.current_chapter_id, **update_data)
                        if not success:
                            raise BusinessException("更新章节内容失败")

                        # 更新进度
                        self.after(0, lambda: update_progress_ui(1, 1, 50, "正在解析台词内容..."))

                        # 解析台词并获取返回值，传入进度回调
                        parsed_lines = self.chapter_controller.parse_content_to_lines(
                            self.project.id, self.current_chapter_id, progress_callback=on_progress
                        )

                        # 完成回调
                        self.after(0, lambda: self.on_import_complete(progress_window, parsed_lines))

                    except Exception as ex:
                        # 错误回调
                        error_msg = str(ex)
                        self.after(0, lambda: self.on_import_error(progress_window, error_msg))

                # 启动线程
                import threading
                thread = threading.Thread(target=run_import_and_parse, daemon=True)
                thread.start()

            except Exception as e:
                messagebox.showerror("错误", f"文件导入失败: {str(e)}")

    def on_import_complete(self, progress_window, parsed_lines):
        """导入完成回调"""
        progress_window.destroy()

        # 显示解析结果统计
        lines_count = len(parsed_lines) if parsed_lines else 0
        messagebox.showinfo("成功", f"文本导入并解析完成！\n共解析出 {lines_count} 条台词")

        # 刷新显示
        try:
            self.load_lines()
            self.load_chapters()  # 刷新章节列表中的台词数量

            # 如果有解析的台词，可以显示一些统计信息
            if parsed_lines:
                roles = set()
                for line in parsed_lines:
                    if hasattr(line, 'role_name'):
                        roles.add(line.role_name)

                if roles:
                    self.chapter_status_var.set(f"解析完成: {lines_count}条台词, {len(roles)}个角色")

        except Exception as e:
            messagebox.showerror("错误", f"刷新失败: {str(e)}")

    def on_import_error(self, progress_window, error_msg):
        """导入错误回调"""
        progress_window.destroy()
        messagebox.showerror("错误", f"导入解析失败: {error_msg}")


    def clear_content(self):
        """清空内容"""
        self.current_chapter_id = None
        self.chapter_status_var.set("请选择章节")

        # 清空台词列表
        for item in self.lines_tree.get_children():
            self.lines_tree.delete(item)

        # 清空台词编辑器
        self.current_line_id = None
        self.line_text.delete(1.0, tk.END)
        self.role_var.set('')
        self.emotion_var.set('')
        self.strength_var.set('')

    # 其他方法保持不变...
    def add_line(self):
        """添加台词"""
        if not self.current_chapter_id:
            messagebox.showwarning("警告", "请先选择章节")
            return

        # 清空编辑器
        self.current_line_id = None
        self.line_text.delete(1.0, tk.END)
        self.line_text.focus()

    def delete_line(self):
        """删除台词"""
        selection = self.lines_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择台词")
            return

        item = self.lines_tree.item(selection[0])
        line_id = item['values'][0]

        try:
            if messagebox.askyesno("确认删除", "确定要删除这条台词吗？"):
                self.line_controller.delete_line(line_id)
                messagebox.showinfo("成功", "台词删除成功")
                self.load_lines()
                self.add_line()  # 清空编辑器
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def save_line(self):
        """保存台词"""
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

            if self.current_line_id:
                # 更新台词
                update_data = {
                    'role_id': role.id,
                    'text_content': text_content,
                    'emotion_id': self.get_emotion_id(self.emotion_var.get()),
                    'strength_id': self.get_strength_id(self.strength_var.get())
                }
                self.line_controller.update_line(self.current_line_id, **update_data)
                messagebox.showinfo("成功", "台词更新成功")
            else:
                # 新建台词
                self.line_controller.create_line(
                    chapter_id=self.current_chapter_id,
                    text_content=text_content,
                    role_id=role.id,
                    emotion_id=self.get_emotion_id(self.emotion_var.get()),
                    strength_id=self.get_strength_id(self.strength_var.get())
                )
                messagebox.showinfo("成功", "台词创建成功")
                self.add_line()  # 清空为下一次输入准备

            self.load_lines()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def generate_audio(self):
        """生成语音"""
        selection = self.lines_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择台词")
            return

        item = self.lines_tree.item(selection[0])
        line_id = item['values'][0]

        try:
            # 这里实现单个台词的语音生成
            messagebox.showinfo("提示", "语音生成功能待实现")
        except Exception as e:
            messagebox.showerror("错误", f"生成失败: {str(e)}")

    def batch_generate(self):
        """批量生成语音"""
        if not self.current_chapter_id:
            messagebox.showwarning("警告", "请先选择章节")
            return

        try:
            # 这里实现批量语音生成
            messagebox.showinfo("提示", "批量生成功能待实现")
        except Exception as e:
            messagebox.showerror("错误", f"批量生成失败: {str(e)}")

    def play_audio(self):
        """播放音频"""
        if not self.current_line_id:
            messagebox.showwarning("警告", "请先选择台词")
            return

        try:
            # 这里实现音频播放
            messagebox.showinfo("提示", "音频播放功能待实现")
        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {str(e)}")

    def edit_audio(self):
        """编辑音频"""
        if not self.current_line_id:
            messagebox.showwarning("警告", "请先选择台词")
            return

        try:
            # 这里实现音频编辑
            messagebox.showinfo("提示", "音频编辑功能待实现")
        except Exception as e:
            messagebox.showerror("错误", f"编辑失败: {str(e)}")

    # 辅助方法
    def get_role_name(self, role_id):
        """获取角色名称"""
        if not role_id:
            return "旁白"
        try:
            roles = self.role_controller.get_roles_by_project(self.project.id)
            role = next((r for r in roles if r.id == role_id), None)
            return role.name if role else "未知"
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
