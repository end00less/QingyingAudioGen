# ui/line_parse_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
from app.core.app_context import AppContext
from app.controllers.base_controller import BusinessException


class LineParseDialog:
    def __init__(self, parent, chapter_id, project, app_controller):
        self.parent = parent
        self.chapter_id = chapter_id
        self.project = project
        self.app_controller = app_controller
        self.chapter_controller = app_controller.chapter_controller
        self.project_controller = app_controller.project_controller

        self.setup_dialog()
        self.load_data()

    def setup_dialog(self):
        """设置台词解析对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("台词解析")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)

        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置框架
        config_frame = ttk.LabelFrame(main_frame, text="解析配置", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # LLM模型选择
        ttk.Label(config_frame, text="LLM模型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.llm_var = tk.StringVar()
        self.llm_combo = ttk.Combobox(config_frame, textvariable=self.llm_var, width=30)
        self.llm_combo.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(5, 20))

        # 精准填充
        self.precise_var = tk.BooleanVar(value=bool(self.project.is_precise_fill))
        ttk.Checkbutton(config_frame, text="启用精准填充", variable=self.precise_var).grid(row=1, column=1, sticky=tk.W,
                                                                                     pady=5)

        # 测试LLM连接
        ttk.Button(config_frame, text="测试LLM连接", command=self.test_llm).grid(row=1, column=3, sticky=tk.W, pady=5)

        # 内容预览框架
        preview_frame = ttk.LabelFrame(main_frame, text="内容预览", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建笔记本控件
        notebook = ttk.Notebook(preview_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 原文标签页
        original_frame = ttk.Frame(notebook, padding="10")
        notebook.add(original_frame, text="原文")

        self.original_text = scrolledtext.ScrolledText(original_frame, wrap=tk.WORD)
        self.original_text.pack(fill=tk.BOTH, expand=True)

        # AI解析标签页
        ai_frame = ttk.Frame(notebook, padding="10")
        notebook.add(ai_frame, text="AI解析")

        self.ai_text = scrolledtext.ScrolledText(ai_frame, wrap=tk.WORD)
        self.ai_text.pack(fill=tk.BOTH, expand=True)

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="开始解析", command=self.start_parse).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="应用到项目", command=self.apply_to_project).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy).pack(side=tk.LEFT)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, pady=(5, 0))

        self.parsed_data = None

    def load_data(self):
        """加载数据"""
        try:
            # 加载章节内容
            chapter = self.chapter_controller.get_chapter(self.chapter_id)
            if chapter and chapter.text_content:
                self.original_text.insert(1.0, chapter.text_content)

            # 加载LLM模型
            if self.project.llm_provider_id:
                llm_provider = self.app_controller.llm_provider_controller.get_llm_provider(
                    self.project.llm_provider_id)
                if llm_provider and llm_provider.model_list:
                    models = llm_provider.model_list if isinstance(llm_provider.model_list, list) else [
                        llm_provider.model_list]
                    self.llm_combo['values'] = models
                    self.llm_var.set(self.project.llm_model or (models[0] if models else ''))

        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def test_llm(self):
        """测试LLM连接"""
        if not self.project.llm_provider_id:
            messagebox.showerror("错误", "未配置LLM服务商")
            return

        model_name = self.llm_var.get()
        if not model_name:
            messagebox.showwarning("警告", "请选择LLM模型")
            return

        try:
            llm_provider = self.app_controller.llm_provider_controller.get_llm_provider(self.project.llm_provider_id)
            self.app_controller.llm_provider_controller.test_llm_provider(
                name=llm_provider.name,
                api_base_url=llm_provider.api_base_url,
                api_key=llm_provider.api_key,
                model_list=llm_provider.model_list,
                custom_params=llm_provider.custom_params
            )
            messagebox.showinfo("成功", "LLM连接测试成功")
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def start_parse(self):
        """开始解析"""
        content = self.original_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("警告", "请先输入或加载文本内容")
            return

        self.status_var.set("解析中...")
        self.ai_text.delete(1.0, tk.END)

        # 在新线程中执行解析
        thread = threading.Thread(target=self._run_parse, args=(content,))
        thread.daemon = True
        thread.start()

    def _run_parse(self, content: str):
        """执行解析"""
        try:
            # 更新章节内容
            self.chapter_controller.update_chapter(self.chapter_id, text_content=content)

            # 解析内容为台词
            lines_data = self.chapter_controller.parse_content_to_lines(self.project.id, self.chapter_id)

            # 显示解析结果
            result_data = [
                {
                    "role_name": line.role_name,
                    "text_content": line.text_content,
                    "emotion_name": line.emotion_name,
                    "strength_name": line.strength_name
                }
                for line in lines_data
            ]

            self.ai_text.insert(1.0, json.dumps(result_data, ensure_ascii=False, indent=2))
            self.parsed_data = result_data
            self.status_var.set(f"解析完成，共解析出 {len(lines_data)} 条台词")

        except BusinessException as e:
            self.status_var.set(f"解析失败: {e.message}")
            messagebox.showerror("错误", e.message)
        except Exception as e:
            self.status_var.set(f"解析失败: {str(e)}")
            messagebox.showerror("错误", f"解析失败: {str(e)}")

    def apply_to_project(self):
        """应用到项目"""
        if not self.parsed_data:
            messagebox.showwarning("警告", "请先完成解析")
            return

        # 确认对话框
        if not messagebox.askyesno("确认", f"确定要将 {len(self.parsed_data)} 条台词应用到项目吗？\n这将覆盖现有的台词数据。"):
            return

        try:
            # 导入台词数据
            json_data = json.dumps(self.parsed_data, ensure_ascii=False)
            self.chapter_controller.import_external_lines(self.project.id, self.chapter_id, json_data)

            messagebox.showinfo("成功", f"成功应用 {len(self.parsed_data)} 条台词到项目")
            self.dialog.destroy()

        except BusinessException as e:
            messagebox.showerror("错误", e.message)