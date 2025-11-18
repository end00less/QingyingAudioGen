# ui/llm_settings_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
from app.controllers.base_controller import BusinessException


class LLMSettingsFrame(ttk.Frame):
    def __init__(self, parent, project, app_controller):
        super().__init__(parent)

        self.parent = parent
        self.project = project
        self.app_controller = app_controller
        self.llm_provider_controller = app_controller.llm_provider_controller

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """设置UI界面"""
        # 创建主容器
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_container, text="🤖 LLM配置",
                                font=("Arial", 16, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 20))

        # 现有服务商选择
        existing_frame = ttk.LabelFrame(main_container, text="选择现有服务商", padding="5")
        existing_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(existing_frame, text="已配置的服务商:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.existing_provider_var = tk.StringVar()
        self.existing_provider_combo = ttk.Combobox(existing_frame,
                                                    textvariable=self.existing_provider_var,
                                                    width=25, state="readonly")
        self.existing_provider_combo.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5, padx=(10, 0))
        self.existing_provider_combo.bind("<<ComboboxSelected>>", self.on_existing_provider_selected)

        ttk.Button(existing_frame, text="刷新列表", command=self.refresh_providers).grid(row=0, column=2, padx=(10, 0))
        ttk.Button(existing_frame, text="删除服务商", command=self.delete_provider).grid(row=0, column=3, padx=(10, 0))

        # 新建/编辑服务商
        config_frame = ttk.LabelFrame(main_container, text="配置服务商", padding="5")
        config_frame.pack(fill=tk.X, pady=(0, 20))

        # 服务商名称
        ttk.Label(config_frame, text="服务商名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.provider_name_var = tk.StringVar()
        self.provider_name_entry = ttk.Entry(config_frame, textvariable=self.provider_name_var, width=25)
        self.provider_name_entry.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5, padx=(10, 0))

        # API Base URL
        ttk.Label(config_frame, text="API Base URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.api_base_url_var = tk.StringVar()
        self.api_base_url_entry = ttk.Entry(config_frame, textvariable=self.api_base_url_var, width=30)
        self.api_base_url_entry.grid(row=1, column=1, sticky=tk.W + tk.E, pady=5, padx=(10, 0))

        # API Key
        ttk.Label(config_frame, text="API Key:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(config_frame, textvariable=self.api_key_var, width=30, show="*")
        self.api_key_entry.grid(row=2, column=1, sticky=tk.W + tk.E, pady=5, padx=(10, 0))

        # 显示/隐藏API Key按钮
        self.show_api_key_btn = ttk.Button(config_frame, text="显示", command=self.toggle_api_key_visibility)
        self.show_api_key_btn.grid(row=2, column=2, padx=(5, 0))

        # 模型列表
        ttk.Label(config_frame, text="模型列表:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.model_list_var = tk.StringVar()
        self.model_list_entry = ttk.Entry(config_frame, textvariable=self.model_list_var, width=30)
        self.model_list_entry.grid(row=3, column=1, sticky=tk.W + tk.E, pady=5, padx=(10, 0))
        ttk.Label(config_frame, text="(用逗号分隔)", font=("Arial", 9)).grid(row=3, column=2, sticky=tk.W, padx=(5, 0))

        # 自定义参数（JSON格式）
        ttk.Label(config_frame, text="自定义参数:").grid(row=4, column=0, sticky=tk.NW, pady=5)
        self.custom_params_text = tk.Text(config_frame, height=4, width=30)
        self.custom_params_text.grid(row=4, column=1, sticky=tk.W + tk.E, pady=5, padx=(10, 0))

        custom_params_scrollbar = ttk.Scrollbar(config_frame, orient=tk.VERTICAL, command=self.custom_params_text.yview)
        self.custom_params_text.configure(yscrollcommand=custom_params_scrollbar.set)
        custom_params_scrollbar.grid(row=4, column=2, sticky=tk.NS, padx=(5, 0))

        # 操作按钮
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=15)

        ttk.Button(btn_frame, text="测试连接", command=self.test_connection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="保存服务商", command=self.save_provider).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="清空表单", command=self.clear_form).pack(side=tk.LEFT)

        # 项目LLM配置
        project_frame = ttk.LabelFrame(main_container, text="项目LLM配置", padding="10")
        project_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(project_frame, text="项目使用服务商:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.project_provider_var = tk.StringVar()
        self.project_provider_combo = ttk.Combobox(project_frame,
                                                   textvariable=self.project_provider_var,
                                                   width=25, state="readonly")
        self.project_provider_combo.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5, padx=(10, 0))
        # 绑定服务商选择事件
        self.project_provider_combo.bind("<<ComboboxSelected>>", self.on_project_provider_selected)

        ttk.Label(project_frame, text="使用模型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.project_model_var = tk.StringVar()
        self.project_model_combo = ttk.Combobox(project_frame,
                                                textvariable=self.project_model_var,
                                                width=25, state="readonly")
        self.project_model_combo.grid(row=1, column=1, sticky=tk.W + tk.E, pady=5, padx=(10, 0))

        # 保存项目配置按钮 - 确保可见
        ttk.Button(project_frame, text="保存项目配置", command=self.save_project_config).grid(
            row=2, column=0, columnspan=2, pady=(15, 5), padx=(0, 10), sticky=tk.W
        )

        # 配置权重
        existing_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(1, weight=1)
        project_frame.columnconfigure(1, weight=1)

    def refresh_providers(self):
        """刷新服务商列表"""
        try:
            providers = self.llm_provider_controller.get_all_llm_providers()
            provider_names = [p.name for p in providers]
            self.existing_provider_combo['values'] = provider_names
            self.project_provider_combo['values'] = provider_names

            if provider_names:
                self.existing_provider_combo.set('')
                self.project_provider_combo.set('')
        except BusinessException as e:
            messagebox.showerror("错误", f"刷新服务商列表失败: {e.message}")

    def on_existing_provider_selected(self, event):
        """选择现有服务商时加载其配置"""
        provider_name = self.existing_provider_var.get()
        if not provider_name:
            return

        try:
            providers = self.llm_provider_controller.get_all_llm_providers()
            selected_provider = next((p for p in providers if p.name == provider_name), None)

            if selected_provider:
                self.provider_name_var.set(selected_provider.name)
                self.api_base_url_var.set(selected_provider.api_base_url or "")
                self.api_key_var.set(selected_provider.api_key or "")
                self.model_list_var.set(selected_provider.model_list or "")

                # 加载自定义参数
                self.custom_params_text.delete(1.0, tk.END)
                if selected_provider.custom_params:
                    try:
                        if isinstance(selected_provider.custom_params, str):
                            self.custom_params_text.insert(1.0, selected_provider.custom_params)
                        else:
                            self.custom_params_text.insert(1.0, json.dumps(selected_provider.custom_params, indent=2,
                                                                           ensure_ascii=False))
                    except:
                        self.custom_params_text.insert(1.0, str(selected_provider.custom_params))

                # 更新项目模型列表
                self.update_project_models()

        except BusinessException as e:
            messagebox.showerror("错误", f"加载服务商配置失败: {e.message}")

    def on_project_provider_selected(self, event):
        """当在项目配置中选择服务商时，更新对应的模型列表"""
        provider_name = self.project_provider_var.get()
        if not provider_name:
            return

        try:
            providers = self.llm_provider_controller.get_all_llm_providers()
            selected_provider = next((p for p in providers if p.name == provider_name), None)

            if selected_provider and selected_provider.model_list:
                # 解析模型列表
                models = [model.strip() for model in selected_provider.model_list.split(',') if model.strip()]
                self.project_model_combo['values'] = models

                # 如果有模型列表，设置第一个为默认值
                if models:
                    self.project_model_combo.set(models[0])
                else:
                    self.project_model_combo.set('')
            else:
                self.project_model_combo['values'] = []
                self.project_model_combo.set('')

        except BusinessException as e:
            messagebox.showerror("错误", f"加载服务商模型列表失败: {e.message}")

    def update_project_models(self):
        """更新项目模型列表"""
        model_list_str = self.model_list_var.get()
        if model_list_str:
            models = [model.strip() for model in model_list_str.split(',')]
            self.project_model_combo['values'] = models
            if models:
                self.project_model_combo.set(models[0])

    def toggle_api_key_visibility(self):
        """切换API Key显示/隐藏"""
        if self.show_api_key_btn['text'] == "显示":
            self.api_key_entry.configure(show="")
            self.show_api_key_btn.configure(text="隐藏")
        else:
            self.api_key_entry.configure(show="*")
            self.show_api_key_btn.configure(text="显示")

    def test_connection(self):
        """测试连接"""
        try:
            # 获取自定义参数
            custom_params_text = self.custom_params_text.get(1.0, tk.END).strip()
            custom_params = {}
            if custom_params_text:
                try:
                    custom_params = json.loads(custom_params_text)
                except json.JSONDecodeError:
                    messagebox.showerror("错误", "自定义参数不是有效的JSON格式")
                    return

            # 清理模型列表
            model_list = self.model_list_var.get().strip()
            model_list_array = [model.strip() for model in model_list.split(',') if model.strip()]

            # 测试连接 - 注意：测试时传入字典和列表，保存时传入 JSON 字符串
            success = self.llm_provider_controller.test_llm_provider(
                name=self.provider_name_var.get(),
                api_base_url=self.api_base_url_var.get(),
                api_key=self.api_key_var.get(),
                model_list=model_list,  # 测试时传入原始字符串
                custom_params=custom_params  # 测试时传入字典
            )

            if success:
                messagebox.showinfo("成功", "连接测试成功！")
            else:
                messagebox.showerror("失败", "连接测试失败")

        except BusinessException as e:
            messagebox.showerror("错误", f"测试连接失败: {e.message}")

    def save_provider(self):
        """保存服务商"""
        try:
            # 将所有变量定义移到 try 块内部
            name = self.provider_name_var.get().strip()
            if not name:
                messagebox.showwarning("警告", "请输入服务商名称")
                return

            api_base_url = self.api_base_url_var.get().strip()
            if not api_base_url:
                messagebox.showwarning("警告", "请输入API Base URL")
                return

            api_key = self.api_key_var.get().strip()
            if not api_key:
                messagebox.showwarning("警告", "请输入API Key")
                return

            model_list = self.model_list_var.get().strip()
            if not model_list:
                messagebox.showwarning("警告", "请输入模型列表")
                return

            # 直接使用 Python 列表，不在前端做 JSON 序列化
            model_list_array = [model.strip() for model in model_list.split(',') if model.strip()]

            # 获取自定义参数
            custom_params_text = self.custom_params_text.get(1.0, tk.END).strip()
            custom_params_dict = {}
            if custom_params_text:
                try:
                    custom_params_dict = json.loads(custom_params_text)
                except json.JSONDecodeError as e:
                    messagebox.showerror("错误", f"自定义参数不是有效的JSON格式: {str(e)}")
                    return

            print(f"前端调试 - 准备传递的数据:")
            print(f"  name: {name}")
            print(f"  model_list: {model_list_array} (type: {type(model_list_array)})")
            print(f"  custom_params: {custom_params_dict} (type: {type(custom_params_dict)})")

            # 检查是否是编辑模式
            existing_providers = self.llm_provider_controller.get_all_llm_providers()
            existing_provider = next((p for p in existing_providers if p.name == name), None)

            if existing_provider:
                # 更新现有服务商
                success = self.llm_provider_controller.update_llm_provider(
                    existing_provider.id,
                    name=name,
                    api_base_url=api_base_url,
                    api_key=api_key,
                    model_list=model_list,  # 直接传递 Python 列表
                    custom_params=custom_params_text  # 直接传递 Python 字典
                )
                if success:
                    messagebox.showinfo("成功", f"服务商 '{name}' 更新成功")
                else:
                    messagebox.showerror("错误", "更新服务商失败")
            else:
                # 创建新服务商
                provider = self.llm_provider_controller.create_llm_provider(
                    name=name,
                    api_base_url=api_base_url,
                    api_key=api_key,
                    model_list=model_list,  # 直接传递 Python 列表
                    custom_params=custom_params_text  # 直接传递 Python 字典
                )
                if provider:
                    messagebox.showinfo("成功", f"服务商 '{name}' 创建成功")
                else:
                    messagebox.showerror("错误", "创建服务商失败")

            # 刷新列表
            self.refresh_providers()

        except BusinessException as e:
            messagebox.showerror("错误", f"保存服务商失败: {e.message}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
            import traceback
            traceback.print_exc()

    def delete_provider(self):
        """删除服务商"""
        provider_name = self.existing_provider_var.get()
        if not provider_name:
            messagebox.showwarning("警告", "请先选择要删除的服务商")
            return

        if not messagebox.askyesno("确认删除", f"确定要删除服务商 '{provider_name}' 吗？"):
            return

        try:
            providers = self.llm_provider_controller.get_all_llm_providers()
            provider = next((p for p in providers if p.name == provider_name), None)

            if provider:
                success = self.llm_provider_controller.delete_llm_provider(provider.id)
                if success:
                    messagebox.showinfo("成功", f"服务商 '{provider_name}' 删除成功")
                    self.clear_form()
                    self.refresh_providers()
                else:
                    messagebox.showerror("错误", "删除服务商失败")
            else:
                messagebox.showerror("错误", "找不到要删除的服务商")

        except BusinessException as e:
            messagebox.showerror("错误", f"删除服务商失败: {e.message}")

    def clear_form(self):
        """清空表单"""
        self.provider_name_var.set("")
        self.api_base_url_var.set("")
        self.api_key_var.set("")
        self.model_list_var.set("")
        self.custom_params_text.delete(1.0, tk.END)
        self.existing_provider_var.set("")

    def save_project_config(self):
        """保存项目配置"""
        if not self.project:
            messagebox.showwarning("警告", "请先打开一个项目")
            return

        provider_name = self.project_provider_var.get()
        model = self.project_model_var.get()

        if not provider_name or not model:
            messagebox.showwarning("警告", "请选择服务商和模型")
            return

        try:
            # 获取服务商ID
            providers = self.llm_provider_controller.get_all_llm_providers()
            provider = next((p for p in providers if p.name == provider_name), None)

            if provider:

                # 构建更新数据字典
                update_data = {
                    "name": self.project.name,  # 必须包含项目名称
                    "llm_provider_id": provider.id,
                    "llm_model": model
                }

                # 调用更新方法，传入字典而不是关键字参数
                success = self.app_controller.project_controller.update_project(
                    self.project.id,
                    **update_data  # 使用 ** 展开字典
                )

                if success:
                    # 更新当前项目的内存对象
                    self.project.llm_provider_id = provider.id
                    self.project.llm_model = model
                    messagebox.showinfo("成功", "项目LLM配置保存成功")
                else:
                    messagebox.showerror("错误", "保存项目配置失败")
            else:
                messagebox.showerror("错误", "找不到选中的服务商")

        except BusinessException as e:
            messagebox.showerror("错误", f"保存项目配置失败: {e.message}")
        except Exception as e:
            messagebox.showerror("错误", f"保存项目配置时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()

    def load_settings(self):
        """加载当前项目的设置"""
        if not self.project:
            return

        try:
            # 刷新服务商列表
            self.refresh_providers()

            # 加载项目当前配置
            if hasattr(self.project, 'llm_provider_id') and self.project.llm_provider_id:
                providers = self.llm_provider_controller.get_all_llm_providers()
                provider = next((p for p in providers if p.id == self.project.llm_provider_id), None)

                if provider:
                    self.project_provider_var.set(provider.name)

                    # 设置模型列表
                    if provider.model_list:
                        models = [model.strip() for model in provider.model_list.split(',') if model.strip()]
                        self.project_model_combo['values'] = models

                    # 设置当前模型
                    if hasattr(self.project, 'llm_model') and self.project.llm_model:
                        self.project_model_var.set(self.project.llm_model)
                        # 如果当前模型不在列表中，添加到列表
                        if self.project.llm_model not in models:
                            self.project_model_combo['values'] = models + [self.project.llm_model]

        except BusinessException as e:
            print(f"加载设置失败: {e.message}")