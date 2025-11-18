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
        self.dialog.geometry("500x400")
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

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)

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

            messagebox.showinfo("成功", "章节保存成功")
            self.dialog.destroy()

        except BusinessException as e:
            messagebox.showerror("错误", f"保存失败: {e.message}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
