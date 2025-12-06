# ui/project_dialog.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
from app.controllers.base_controller import BusinessException


class ProjectDialog:
    def __init__(self, parent, project_controller):
        self.project_controller = project_controller
        self.result = None

        # 创建现代化对话框 - 保持紧凑尺寸
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("新建项目")
        self.dialog.geometry("600x700")  # 保持紧凑尺寸
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 设置对话框居中
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.setup_ui()
        self.load_providers()

    def setup_ui(self):
        """设置UI界面"""
        # 主容器 - 保持紧凑内边距
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # 标题 - 稍微增大字体
        title_label = ctk.CTkLabel(
            main_frame,
            text="📁 创建新项目",
            font=ctk.CTkFont(size=19, weight="bold")  # 从 18 改为 19
        )
        title_label.pack(pady=(0, 15))

        # 项目名称 - 增大字体
        name_frame = ctk.CTkFrame(main_frame)
        name_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            name_frame,
            text="项目名称:",
            font=ctk.CTkFont(size=14, weight="bold")  # 从 13 改为 14
        ).pack(anchor="w", pady=(0, 3))

        self.name_var = ctk.StringVar()
        name_entry = ctk.CTkEntry(
            name_frame,
            textvariable=self.name_var,
            placeholder_text="输入项目名称...",
            height=35
        )
        name_entry.pack(fill="x")

        # 项目描述 - 增大字体
        desc_frame = ctk.CTkFrame(main_frame)
        desc_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            desc_frame,
            text="项目描述:",
            font=ctk.CTkFont(size=14, weight="bold")  # 从 13 改为 14
        ).pack(anchor="w", pady=(0, 3))

        self.desc_text = ctk.CTkTextbox(
            desc_frame,
            height=70
        )
        self.desc_text.pack(fill="x")

        # 添加默认提示文本
        self.desc_text.insert("0.0", "在此输入项目描述...")

        # 项目路径 - 增大字体
        path_frame = ctk.CTkFrame(main_frame)
        path_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            path_frame,
            text="项目路径:",
            font=ctk.CTkFont(size=14, weight="bold")  # 从 13 改为 14
        ).pack(anchor="w", pady=(0, 3))

        path_input_frame = ctk.CTkFrame(path_frame)
        path_input_frame.pack(fill="x")

        self.path_var = ctk.StringVar()
        path_entry = ctk.CTkEntry(
            path_input_frame,
            textvariable=self.path_var,
            placeholder_text="选择项目保存路径...",
            height=35
        )
        path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        browse_btn = ctk.CTkButton(
            path_input_frame,
            text="📂 浏览",
            command=self.browse_path,
            width=70,
            height=35
        )
        browse_btn.pack(side="right")

        # LLM配置区域 - 增大字体
        llm_frame = ctk.CTkFrame(main_frame)
        llm_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            llm_frame,
            text="🤖 LLM配置",
            font=ctk.CTkFont(size=14, weight="bold")  # 从 13 改为 14
        ).pack(anchor="w", pady=(0, 8))

        # 将LLM提供商和模型放在同一行
        llm_row_frame = ctk.CTkFrame(llm_frame)
        llm_row_frame.pack(fill="x")

        # LLM提供商 - 左侧
        provider_frame = ctk.CTkFrame(llm_row_frame)
        provider_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            provider_frame,
            text="LLM提供商:",
            font=ctk.CTkFont(size=12)  # 从 11 改为 12
        ).pack(anchor="w", pady=(0, 3))

        self.llm_provider_var = ctk.StringVar()
        self.llm_provider_combo = ctk.CTkComboBox(
            provider_frame,
            variable=self.llm_provider_var,
            height=35,
            command=self.on_llm_provider_changed
        )
        self.llm_provider_combo.pack(fill="x")

        # LLM模型 - 右侧
        model_frame = ctk.CTkFrame(llm_row_frame)
        model_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            model_frame,
            text="LLM模型:",
            font=ctk.CTkFont(size=12)  # 从 11 改为 12
        ).pack(anchor="w", pady=(0, 3))

        self.llm_model_var = ctk.StringVar()
        self.llm_model_combo = ctk.CTkComboBox(
            model_frame,
            variable=self.llm_model_var,
            height=35
        )
        self.llm_model_combo.pack(fill="x")

        # TTS配置区域 - 增大字体
        tts_frame = ctk.CTkFrame(main_frame)
        tts_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            tts_frame,
            text="🔊 TTS配置",
            font=ctk.CTkFont(size=14, weight="bold")  # 从 13 改为 14
        ).pack(anchor="w", pady=(0, 8))

        # TTS引擎
        tts_provider_frame = ctk.CTkFrame(tts_frame)
        tts_provider_frame.pack(fill="x")

        ctk.CTkLabel(
            tts_provider_frame,
            text="TTS引擎:",
            font=ctk.CTkFont(size=12)  # 从 11 改为 12
        ).pack(anchor="w", pady=(0, 3))

        self.tts_provider_var = ctk.StringVar()
        self.tts_provider_combo = ctk.CTkComboBox(
            tts_provider_frame,
            variable=self.tts_provider_var,
            height=35
        )
        self.tts_provider_combo.pack(fill="x")

        # 高级选项 - 增大字体
        advanced_frame = ctk.CTkFrame(main_frame)
        advanced_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(
            advanced_frame,
            text="⚙️ 高级选项",
            font=ctk.CTkFont(size=14, weight="bold")  # 从 13 改为 14
        ).pack(anchor="w", pady=(0, 8))

        # 精确填充选项 - 增大字体
        self.is_precise_fill_var = ctk.BooleanVar(value=False)
        precise_fill_check = ctk.CTkCheckBox(
            advanced_frame,
            text="启用精确填充（提高配音精度，但可能增加处理时间）",
            variable=self.is_precise_fill_var,
            font=ctk.CTkFont(size=12)  # 从 11 改为 12
        )
        precise_fill_check.pack(anchor="w")

        # 按钮区域 - 增大字体
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=(15, 0))

        # 创建按钮容器
        button_container = ctk.CTkFrame(btn_frame)
        button_container.pack(expand=True)

        # 创建按钮 - 增大字体
        create_btn = ctk.CTkButton(
            button_container,
            text="✅ 创建项目",
            command=self.create_project,
            height=40,
            width=100,
            font=ctk.CTkFont(size=14, weight="bold"),  # 从 13 改为 14
            fg_color="#2ecc71",
            hover_color="#27ae60"
        )
        create_btn.pack(side="left", padx=(0, 8))

        # 取消按钮 - 增大字体
        cancel_btn = ctk.CTkButton(
            button_container,
            text="❌ 取消",
            command=self.dialog.destroy,
            height=40,
            width=100,
            font=ctk.CTkFont(size=14, weight="bold"),  # 从 13 改为 14
            fg_color="#e74c3c",
            hover_color="#c0392b"
        )
        cancel_btn.pack(side="left")

    def load_providers(self):
        """从数据库加载提供商数据"""
        try:
            # 加载LLM提供商
            llm_providers = self.project_controller.get_llm_providers()
            provider_names = [provider.name for provider in llm_providers]
            self.llm_provider_combo.configure(values=provider_names)

            # 加载TTS提供商
            tts_providers = self.project_controller.get_tts_providers()
            tts_names = [provider.name for provider in tts_providers]
            self.tts_provider_combo.configure(values=tts_names)

            # 设置默认选择（如果有的话）
            if provider_names:
                self.llm_provider_var.set(provider_names[0])
                self.on_llm_provider_changed(provider_names[0])
            if tts_names:
                self.tts_provider_var.set(tts_names[0])

        except Exception as e:
            messagebox.showerror("错误", f"加载提供商数据失败: {str(e)}")

    def on_llm_provider_changed(self, selected_value=None):
        """LLM提供商改变时更新模型列表"""
        # 如果通过 command 调用，selected_value 就是选中的值
        # 如果通过其他方式调用，可以从变量中获取
        if selected_value is None:
            selected_provider = self.llm_provider_var.get()
        else:
            selected_provider = selected_value

        if not selected_provider:
            return

        try:
            # 获取选中提供商的模型列表
            models = self.project_controller.get_llm_models_by_provider(selected_provider)
            model_names = [model for model in models]  # 假设返回的是模型名称列表

            self.llm_model_combo.configure(values=model_names)
            if model_names:
                self.llm_model_var.set(model_names[0])
            else:
                self.llm_model_var.set('')

        except Exception as e:
            messagebox.showerror("错误", f"加载模型列表失败: {str(e)}")

    def browse_path(self):
        """浏览选择项目路径"""
        path = filedialog.askdirectory(title="选择项目保存路径")
        if path:
            self.path_var.set(path)

    def create_project(self):
        """创建项目"""
        try:
            name = self.name_var.get().strip()

            # 获取描述文本
            description = self.desc_text.get("1.0", "end").strip()

            # 如果用户没有修改默认提示文本，则清空
            if description == "在此输入项目描述...":
                description = ""

            path = self.path_var.get().strip()
            llm_provider_name = self.llm_provider_var.get()
            llm_model = self.llm_model_var.get()
            tts_provider_name = self.tts_provider_var.get()
            is_precise_fill = self.is_precise_fill_var.get()

            # 验证必填字段
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
                is_precise_fill=is_precise_fill
            )

            # 显示成功消息
            messagebox.showinfo("成功", f"项目 '{name}' 创建成功！")
            self.dialog.destroy()

        except BusinessException as e:
            messagebox.showerror("错误", e.message)
        except Exception as e:
            messagebox.showerror("错误", f"创建项目失败: {str(e)}")
