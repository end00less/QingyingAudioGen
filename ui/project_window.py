# ui/project_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from app.controllers.base_controller import BusinessException


class ProjectDialog:
    def __init__(self, parent, project_controller):
        self.project_controller = project_controller
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("新建项目")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()
        self.load_providers()

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 项目名称
        ttk.Label(main_frame, text="项目名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 项目描述
        ttk.Label(main_frame, text="项目描述:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.desc_text = tk.Text(main_frame, width=40, height=4)
        self.desc_text.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 项目路径
        ttk.Label(main_frame, text="项目路径:").grid(row=2, column=0, sticky=tk.W, pady=5)
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=30)
        path_entry.pack(side=tk.LEFT)

        ttk.Button(path_frame, text="浏览", command=self.browse_path).pack(side=tk.LEFT, padx=(5, 0))

        # LLM提供商
        ttk.Label(main_frame, text="LLM提供商:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.llm_provider_var = tk.StringVar()
        self.llm_provider_combo = ttk.Combobox(main_frame, textvariable=self.llm_provider_var,
                                               width=37, state="readonly")
        self.llm_provider_combo.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.llm_provider_combo.bind('<<ComboboxSelected>>', self.on_llm_provider_changed)

        # LLM模型
        ttk.Label(main_frame, text="LLM模型:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.llm_model_var = tk.StringVar()
        self.llm_model_combo = ttk.Combobox(main_frame, textvariable=self.llm_model_var,
                                            width=37, state="readonly")
        self.llm_model_combo.grid(row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # TTS引擎
        ttk.Label(main_frame, text="TTS引擎:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.tts_provider_var = tk.StringVar()
        self.tts_provider_combo = ttk.Combobox(main_frame, textvariable=self.tts_provider_var,
                                               width=37, state="readonly")
        self.tts_provider_combo.grid(row=5, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 精确填充选项
        self.is_precise_fill_var = tk.BooleanVar(value=False)
        precise_fill_check = ttk.Checkbutton(
            main_frame,
            text="启用精确填充",
            variable=self.is_precise_fill_var
        )
        precise_fill_check.grid(row=6, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="创建", command=self.create_project).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT)

        # 设置列权重
        main_frame.columnconfigure(1, weight=1)

    def load_providers(self):
        """从数据库加载提供商数据"""
        try:
            # 加载LLM提供商
            llm_providers = self.project_controller.get_llm_providers()
            provider_names = [provider.name for provider in llm_providers]
            self.llm_provider_combo['values'] = provider_names

            # 加载TTS提供商
            tts_providers = self.project_controller.get_tts_providers()
            tts_names = [provider.name for provider in tts_providers]
            self.tts_provider_combo['values'] = tts_names

            # 设置默认选择（如果有的话）
            if provider_names:
                self.llm_provider_var.set(provider_names[0])
                self.on_llm_provider_changed()
            if tts_names:
                self.tts_provider_var.set(tts_names[0])

        except Exception as e:
            messagebox.showerror("错误", f"加载提供商数据失败: {str(e)}")

    def on_llm_provider_changed(self, event=None):
        """LLM提供商改变时更新模型列表"""
        selected_provider = self.llm_provider_var.get()
        if not selected_provider:
            return

        try:
            # 获取选中提供商的模型列表
            models = self.project_controller.get_llm_models_by_provider(selected_provider)
            model_names = [model for model in models]  # 假设返回的是模型名称列表

            self.llm_model_combo['values'] = model_names
            if model_names:
                self.llm_model_var.set(model_names[0])
            else:
                self.llm_model_var.set('')

        except Exception as e:
            messagebox.showerror("错误", f"加载模型列表失败: {str(e)}")

    def browse_path(self):
        """浏览选择项目路径"""
        from tkinter import filedialog
        path = filedialog.askdirectory(title="选择项目保存路径")
        if path:
            self.path_var.set(path)

    def create_project(self):
        """创建项目"""
        try:
            name = self.name_var.get().strip()
            description = self.desc_text.get("1.0", tk.END).strip()
            path = self.path_var.get().strip()
            llm_provider_name = self.llm_provider_var.get()
            llm_model = self.llm_model_var.get()
            tts_provider_name = self.tts_provider_var.get()
            is_precise_fill = self.is_precise_fill_var.get()

            if not name:
                messagebox.showwarning("警告", "请输入项目名称")
                return

            if not path:
                messagebox.showwarning("警告", "请选择项目路径")
                return

            if not llm_provider_name:
                messagebox.showwarning("警告", "请选择LLM提供商")
                return

            if not llm_model:
                messagebox.showwarning("警告", "请选择LLM模型")
                return

            if not tts_provider_name:
                messagebox.showwarning("警告", "请选择TTS引擎")
                return

            # 获取提供商ID
            llm_provider_id = self.project_controller.get_llm_provider_id_by_name(llm_provider_name)
            tts_provider_id = self.project_controller.get_tts_provider_id_by_name(tts_provider_name)

            if not llm_provider_id:
                messagebox.showerror("错误", f"未找到LLM提供商: {llm_provider_name}")
                return

            if not tts_provider_id:
                messagebox.showerror("错误", f"未找到TTS提供商: {tts_provider_name}")
                return

            # 创建项目
            self.result = self.project_controller.create_project(
                name=name,
                description=description,
                project_root_path=path,
                llm_provider_id=llm_provider_id,
                llm_model=llm_model,
                tts_provider_id=tts_provider_id,
                is_precise_fill=is_precise_fill  # 添加精确填充参数
            )

            self.dialog.destroy()

        except BusinessException as e:
            messagebox.showerror("错误", e.message)
        except Exception as e:
            messagebox.showerror("错误", f"创建项目失败: {str(e)}")