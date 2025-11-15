# ui/project_window.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from app.controllers.base_controller import BusinessException

class ProjectDialog:
    def __init__(self, parent, project_controller, project=None):
        self.project_controller = project_controller
        self.project = project
        self.result = False

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑项目" if project else "新建项目")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()
        if project:
            self.load_project_data()

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 项目名称
        ttk.Label(main_frame, text="项目名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        # 项目描述
        ttk.Label(main_frame, text="项目描述:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.desc_text = tk.Text(main_frame, width=40, height=4)
        self.desc_text.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # 项目路径
        ttk.Label(main_frame, text="项目路径:").grid(row=2, column=0, sticky=tk.W, pady=5)
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=35)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(path_frame, text="浏览", command=self.browse_path).pack(side=tk.RIGHT, padx=(5, 0))

        # LLM配置
        ttk.Label(main_frame, text="LLM模型:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.llm_var = tk.StringVar()
        self.llm_combo = ttk.Combobox(main_frame, textvariable=self.llm_var, width=37)
        self.llm_combo['values'] = ('gpt-3.5-turbo', 'gpt-4', 'claude-3', '其他')
        self.llm_combo.grid(row=3, column=1, sticky=tk.W, pady=5)

        # 精准填充
        self.precise_var = tk.BooleanVar()
        self.precise_check = ttk.Checkbutton(main_frame, text="启用精准填充", variable=self.precise_var)
        self.precise_check.grid(row=4, column=1, sticky=tk.W, pady=5)

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(btn_frame, text="保存", command=self.save_project2).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT)

        # 配置权重
        main_frame.columnconfigure(1, weight=1)

    def browse_path(self):
        """选择项目路径"""
        path = filedialog.askdirectory(title="选择项目保存路径")
        if path:
            self.path_var.set(path)

    def load_project_data(self):
        """加载项目数据"""
        if self.project:
            self.name_var.set(self.project.name)
            self.desc_text.insert(1.0, self.project.description or '')
            self.path_var.set(self.project.project_root_path or '')
            self.llm_var.set(self.project.llm_model or '')
            self.precise_var.set(bool(self.project.is_precise_fill))

    def save_project(self):
        """通过 Controller 保存项目"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入项目名称")
            return

        description = self.desc_text.get(1.0, tk.END).strip()
        project_path = self.path_var.get().strip()

        if not project_path:
            messagebox.showwarning("警告", "请选择项目保存路径")
            return

        try:
            if self.project:
                # 更新项目
                update_data = {
                    'name': name,
                    'description': description,
                    'project_root_path': project_path,
                    'llm_model': self.llm_var.get(),
                    'is_precise_fill': 1 if self.precise_var.get() else 0
                }
                result = self.project_controller.update_project(self.project.id, **update_data)
                messagebox.showinfo("成功", "项目更新成功")
            else:
                # 新建项目
                result = self.project_controller.create_project(
                    name=name,
                    description=description,
                    project_root_path=project_path
                )
                messagebox.showinfo("成功", "项目创建成功")

            self.result = True
            self.dialog.destroy()

        except BusinessException as e:
            messagebox.showerror("错误", e.message)
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    def save_project2(self):
        """通过 Controller 保存项目"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "请输入项目名称")
            return

        description = self.desc_text.get(1.0, tk.END).strip()
        project_path = self.path_var.get().strip()

        if not project_path:
            messagebox.showwarning("警告", "请选择项目保存路径")
            return

        try:
            if self.project:
                # 更新项目
                update_data = {
                    'name': name,
                    'description': description,
                    'project_root_path': project_path,
                    'llm_model': self.llm_var.get(),
                    'is_precise_fill': 1 if self.precise_var.get() else 0
                }
                result = self.project_controller.update_project(self.project.id, **update_data)
                messagebox.showinfo("成功", "项目更新成功")
                self.result = result  # 返回更新后的 Entity
            else:
                # 新建项目
                result = self.project_controller.create_project(
                    name=name,
                    description=description,
                    project_root_path=project_path,
                    llm_model=self.llm_var.get(),
                    is_precise_fill=1 if self.precise_var.get() else 0
                )
                messagebox.showinfo("成功", "项目创建成功")
                self.result = result  # 返回新建的 Entity

            self.dialog.destroy()

        except BusinessException as e:
            messagebox.showerror("错误", e.message)
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
