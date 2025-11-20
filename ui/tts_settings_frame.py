# app/ui/tts_settings_frame.py
import tkinter as tk
from tkinter import ttk, messagebox
import json
from app.controllers.base_controller import BusinessException


class TTSSettingsFrame(ttk.Frame):
    def __init__(self, parent, project, app_controller):
        super().__init__(parent)

        self.parent = parent
        self.project = project
        self.app_controller = app_controller
        self.tts_provider_controller = app_controller.tts_provider_controller

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """设置UI界面"""
        # 创建主容器
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_container, text="🔊 TTS配置",
                                font=("Arial", 16, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 20))

        # 现有服务商选择
        existing_frame = ttk.LabelFrame(main_container, text="选择现有TTS服务商", padding="5")
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
        config_frame = ttk.LabelFrame(main_container, text="配置TTS服务商", padding="5")
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

        # 状态
        ttk.Label(config_frame, text="状态:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="1")
        status_frame = ttk.Frame(config_frame)
        status_frame.grid(row=3, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Radiobutton(status_frame, text="启用", variable=self.status_var, value="1").pack(side=tk.LEFT)
        ttk.Radiobutton(status_frame, text="禁用", variable=self.status_var, value="0").pack(side=tk.LEFT, padx=(10, 0))

        # 操作按钮
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=15)

        ttk.Button(btn_frame, text="测试连接", command=self.test_connection).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="保存服务商", command=self.save_provider).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="清空表单", command=self.clear_form).pack(side=tk.LEFT)

        # 项目TTS配置
        project_frame = ttk.LabelFrame(main_container, text="项目TTS配置", padding="10")
        project_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(project_frame, text="项目使用服务商:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.project_provider_var = tk.StringVar()
        self.project_provider_combo = ttk.Combobox(project_frame,
                                                   textvariable=self.project_provider_var,
                                                   width=25, state="readonly")
        self.project_provider_combo.grid(row=0, column=1, sticky=tk.W + tk.E, pady=5, padx=(10, 0))

        # 保存项目配置按钮
        ttk.Button(project_frame, text="保存项目配置", command=self.save_project_config).grid(
            row=1, column=0, columnspan=2, pady=(15, 5), padx=(0, 10), sticky=tk.W
        )

        # 配置权重
        existing_frame.columnconfigure(1, weight=1)
        config_frame.columnconfigure(1, weight=1)
        project_frame.columnconfigure(1, weight=1)

    def refresh_providers(self):
        """刷新TTS服务商列表"""
        try:
            providers = self.tts_provider_controller.get_all_tts_providers()
            provider_names = [p.name for p in providers if p.status != 0]  # 只显示启用的服务商
            self.existing_provider_combo['values'] = provider_names
            self.project_provider_combo['values'] = provider_names

            if provider_names:
                self.existing_provider_combo.set('')
                self.project_provider_combo.set('')
        except BusinessException as e:
            messagebox.showerror("错误", f"刷新TTS服务商列表失败: {e.message}")

    def on_existing_provider_selected(self, event):
        """选择现有TTS服务商时加载其配置"""
        provider_name = self.existing_provider_var.get()
        if not provider_name:
            return

        try:
            providers = self.tts_provider_controller.get_all_tts_providers()
            selected_provider = next((p for p in providers if p.name == provider_name), None)

            if selected_provider:
                self.provider_name_var.set(selected_provider.name)
                self.api_base_url_var.set(selected_provider.api_base_url or "")
                self.api_key_var.set(selected_provider.api_key or "")
                self.status_var.set(str(selected_provider.status or "1"))

        except BusinessException as e:
            messagebox.showerror("错误", f"加载TTS服务商配置失败: {e.message}")

    def toggle_api_key_visibility(self):
        """切换API Key显示/隐藏"""
        if self.show_api_key_btn['text'] == "显示":
            self.api_key_entry.configure(show="")
            self.show_api_key_btn.configure(text="隐藏")
        else:
            self.api_key_entry.configure(show="*")
            self.show_api_key_btn.configure(text="显示")

    def test_connection(self):
        """测试TTS服务商连接"""
        try:
            name = self.provider_name_var.get().strip()
            api_base_url = self.api_base_url_var.get().strip()
            api_key = self.api_key_var.get().strip()

            if not name:
                messagebox.showwarning("警告", "请输入服务商名称")
                return
            if not api_base_url:
                messagebox.showwarning("警告", "请输入API Base URL")
                return

            # 测试连接
            success = self.tts_provider_controller.test_tts_provider(
                name=name,
                api_base_url=api_base_url,
                api_key=api_key
            )

            if success:
                messagebox.showinfo("成功", "TTS服务商连接测试成功！")
            else:
                messagebox.showerror("失败", "TTS服务商连接测试失败")

        except BusinessException as e:
            messagebox.showerror("错误", f"测试连接失败: {e.message}")

    def save_provider(self):
        """保存TTS服务商"""
        try:
            name = self.provider_name_var.get().strip()
            api_base_url = self.api_base_url_var.get().strip()
            api_key = self.api_key_var.get().strip()
            status = int(self.status_var.get())

            if not name:
                messagebox.showwarning("警告", "请输入服务商名称")
                return
            if not api_base_url:
                messagebox.showwarning("警告", "请输入API Base URL")
                return

            # 检查是否是编辑模式
            existing_providers = self.tts_provider_controller.get_all_tts_providers()
            existing_provider = next((p for p in existing_providers if p.name == name), None)

            if existing_provider:
                # 更新现有服务商
                update_data = {
                    "name": name,
                    "api_base_url": api_base_url,
                    "api_key": api_key,
                    "status": status
                }
                success = self.tts_provider_controller.update_tts_provider(
                    existing_provider.id,
                    **update_data
                )
                if success:
                    messagebox.showinfo("成功", f"TTS服务商 '{name}' 更新成功")
                else:
                    messagebox.showerror("错误", "更新TTS服务商失败")
            else:
                # 创建新服务商
                provider = self.tts_provider_controller.create_tts_provider(
                    name=name,
                    api_base_url=api_base_url,
                    api_key=api_key,
                    status=status
                )
                if provider:
                    messagebox.showinfo("成功", f"TTS服务商 '{name}' 创建成功")
                else:
                    messagebox.showerror("错误", "创建TTS服务商失败")

            # 刷新列表
            self.refresh_providers()

        except BusinessException as e:
            messagebox.showerror("错误", f"保存TTS服务商失败: {e.message}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    def delete_provider(self):
        """删除TTS服务商"""
        provider_name = self.existing_provider_var.get()
        if not provider_name:
            messagebox.showwarning("警告", "请先选择要删除的服务商")
            return

        if not messagebox.askyesno("确认删除", f"确定要删除TTS服务商 '{provider_name}' 吗？"):
            return

        try:
            providers = self.tts_provider_controller.get_all_tts_providers()
            provider = next((p for p in providers if p.name == provider_name), None)

            if provider:
                success = self.tts_provider_controller.delete_tts_provider(provider.id)
                if success:
                    messagebox.showinfo("成功", f"TTS服务商 '{provider_name}' 删除成功")
                    self.clear_form()
                    self.refresh_providers()
                else:
                    messagebox.showerror("错误", "删除TTS服务商失败")
            else:
                messagebox.showerror("错误", "找不到要删除的TTS服务商")

        except BusinessException as e:
            messagebox.showerror("错误", f"删除TTS服务商失败: {e.message}")


    def clear_form(self):
        """清空表单"""
        self.provider_name_var.set("")
        self.api_base_url_var.set("")
        self.api_key_var.set("")
        self.status_var.set("1")
        self.existing_provider_var.set("")

    def save_project_config(self):
        """保存项目TTS配置"""
        if not self.project:
            messagebox.showwarning("警告", "请先打开一个项目")
            return

        provider_name = self.project_provider_var.get()

        if not provider_name:
            messagebox.showwarning("警告", "请选择TTS服务商")
            return

        try:
            # 获取服务商ID
            providers = self.tts_provider_controller.get_all_tts_providers()
            provider = next((p for p in providers if p.name == provider_name), None)

            if provider:
                # 构建更新数据字典
                update_data = {
                    "name": self.project.name,
                    "tts_provider_id": provider.id
                }

                # 调用更新方法
                success = self.app_controller.project_controller.update_project(
                    self.project.id,
                    **update_data
                )

                if success:
                    # 更新当前项目的内存对象
                    self.project.tts_provider_id = provider.id
                    messagebox.showinfo("成功", "项目TTS配置保存成功")
                else:
                    messagebox.showerror("错误", "保存项目TTS配置失败")
            else:
                messagebox.showerror("错误", "找不到选中的TTS服务商")

        except BusinessException as e:
            messagebox.showerror("错误", f"保存项目TTS配置失败: {e.message}")
        except Exception as e:
            messagebox.showerror("错误", f"保存项目TTS配置时发生错误: {str(e)}")

    def load_settings(self):
        """加载当前项目的TTS设置"""
        if not self.project:
            return

        try:
            # 刷新服务商列表
            self.refresh_providers()

            # 加载项目当前配置
            if hasattr(self.project, 'tts_provider_id') and self.project.tts_provider_id:
                providers = self.tts_provider_controller.get_all_tts_providers()
                provider = next((p for p in providers if p.id == self.project.tts_provider_id), None)

                if provider:
                    self.project_provider_var.set(provider.name)

        except BusinessException as e:
            print(f"加载TTS设置失败: {e.message}")