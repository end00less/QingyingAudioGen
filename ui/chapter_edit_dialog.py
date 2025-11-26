# ui/chapter_edit_dialog.py - 修复版本
import tkinter as tk
from tkinter import ttk, messagebox
from app.controllers.base_controller import BusinessException


class ChapterEditDialog:
    def __init__(self, parent, chapter_controller, project_id, chapter=None, initial_content=None):
        self.parent = parent
        self.chapter_controller = chapter_controller
        self.project_id = project_id  # 保存项目ID
        self.chapter = chapter
        self.result = None

        self.setup_dialog()
        if chapter:
            self.load_chapter_data()
        elif initial_content:
            self.content_text.insert(1.0, initial_content)

    def setup_dialog(self):
        """设置对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑章节" if self.chapter else "新建章节")
        self.dialog.geometry("500x450")  # 增加高度以容纳新选项
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 章节标题
        ttk.Label(main_frame, text="章节标题:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var, width=40)
        self.title_entry.grid(row=0, column=1, sticky=tk.W, pady=5)

        # 添加提示文本
        if not self.chapter:
            self.title_entry.insert(0, "第一章 回国")
            self.title_entry.select_range(0, tk.END)
            self.title_entry.focus()

        # 章节内容
        ttk.Label(main_frame, text="章节内容:").grid(row=1, column=0, sticky=tk.NW, pady=5)

        # 内容文本框
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=1, column=1, sticky=tk.W + tk.E, pady=5)

        self.content_text = tk.Text(text_frame, width=40, height=15, wrap=tk.WORD)
        content_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.content_text.yview)
        self.content_text.configure(yscrollcommand=content_scrollbar.set)

        self.content_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        content_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 自动分词选项（只在新建章节时显示）
        if not self.chapter:
            self.auto_parse_var = tk.BooleanVar(value=True)  # 默认选中
            auto_parse_check = ttk.Checkbutton(
                main_frame,
                text="自动分词（使用LLM解析台词）",
                variable=self.auto_parse_var
            )
            auto_parse_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=10)

            # 添加说明文本
            help_label = ttk.Label(
                main_frame,
                text="勾选后将在保存章节时自动调用LLM服务解析台词内容",
                font=("Arial", 8),
                foreground="gray"
            )
            help_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        else:
            # 编辑现有章节时不显示自动分词选项
            self.auto_parse_var = tk.BooleanVar(value=False)

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="保存", command=self.save_chapter).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT)

        # 配置权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def load_chapter_data(self):
        """加载章节数据"""
        if self.chapter:
            self.title_var.set(self.chapter.title)
            self.content_text.insert(1.0, self.chapter.text_content or '')

    def save_chapter(self):
        """保存章节"""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("警告", "请输入章节标题")
            return

        content = self.content_text.get(1.0, tk.END).strip()
        auto_parse = self.auto_parse_var.get()

        try:
            if self.chapter:
                # 更新章节 - 关键修复：传递正确的参数格式
                # 服务层期望 data 字典包含 title 和 project_id
                update_data = {
                    'title': title,
                    'project_id': self.project_id,  # 必须传递 project_id
                    'text_content': content
                }

                success = self.chapter_controller.update_chapter(self.chapter.id, **update_data)

                if not success:
                    messagebox.showerror("错误", "章节更新失败，可能存在同名章节")
                    return

                # 重新获取章节数据
                self.result = self.chapter_controller.get_chapter(self.chapter.id)
                if not self.result:
                    # 如果获取失败，使用原始数据
                    self.result = self.chapter
                    self.result.title = title
                    self.result.text_content = content
            else:
                # 创建章节
                self.result = self.chapter_controller.create_chapter(
                    project_id=self.project_id,
                    title=title,
                    text_content=content
                )

                # 如果勾选了自动分词且章节创建成功，则调用LLM进行分词
                if auto_parse and self.result and content.strip():
                    self.auto_parse_content(self.result.id, content)

            messagebox.showinfo("成功", "章节保存成功")
            self.dialog.destroy()

        except BusinessException as e:
            messagebox.showerror("错误", f"保存失败: {e.message}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    def auto_parse_content(self, chapter_id, content):
        """自动调用LLM进行分词"""
        try:
            # 显示进度窗口
            progress_window = tk.Toplevel(self.dialog)
            progress_window.title("自动分词")
            progress_window.geometry("400x120")
            progress_window.transient(self.dialog)
            progress_window.grab_set()
            progress_window.resizable(False, False)

            progress_frame = ttk.Frame(progress_window, padding="20")
            progress_frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(progress_frame, text="正在使用LLM自动分词，请稍候...",
                      font=("Arial", 10, "bold")).pack(pady=(0, 10))

            progress_status = ttk.Label(progress_frame, text="准备中...")
            progress_status.pack(pady=5)

            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_frame, variable=progress_var,
                                           maximum=100, mode='indeterminate')
            progress_bar.pack(fill=tk.X, pady=10)
            progress_bar.start()

            def run_parse():
                try:
                    # 调用章节控制器的分词方法
                    parsed_lines = self.chapter_controller.parse_content_to_lines(
                        self.project_id, chapter_id
                    )

                    # 完成回调
                    self.dialog.after(0, lambda: self.on_parse_complete(
                        progress_window,
                        len(parsed_lines) if parsed_lines else 0
                    ))

                except Exception as e:
                    # 错误回调
                    error_msg = str(e)
                    self.dialog.after(0, lambda: self.on_parse_error(progress_window, error_msg))

            # 启动线程
            import threading
            thread = threading.Thread(target=run_parse, daemon=True)
            thread.start()

        except Exception as e:
            print(f"自动分词启动失败: {e}")

    def on_parse_complete(self, progress_window, lines_count):
        """分词完成回调"""
        progress_window.destroy()
        if lines_count > 0:
            messagebox.showinfo("分词完成", f"自动分词完成！共解析出 {lines_count} 条台词")
        else:
            messagebox.showinfo("分词完成", "自动分词完成，但未解析出台词")

    def on_parse_error(self, progress_window, error_msg):
        """分词错误回调"""
        progress_window.destroy()
        messagebox.showwarning("分词失败", f"自动分词失败: {error_msg}\n\n您可以在章节编辑器中手动导入文本进行分词。")