# ui/project_selection_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from app.controllers.base_controller import BusinessException


class ProjectSelectionDialog:
    def __init__(self, parent, project_controller):
        self.project_controller = project_controller
        self.selected_project = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("打开项目")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.setup_ui()
        self.load_projects()

    def setup_ui(self):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(main_frame, text="选择要打开的项目",
                                font=("Arial", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))

        # 项目列表框架
        list_frame = ttk.LabelFrame(main_frame, text="项目列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 创建树形视图显示项目
        columns = ("name", "description", "created_at", "path")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)

        # 设置列标题
        self.tree.heading("name", text="项目名称")
        self.tree.heading("description", text="描述")
        self.tree.heading("created_at", text="创建时间")
        self.tree.heading("path", text="项目路径")

        # 设置列宽
        self.tree.column("name", width=120)
        self.tree.column("description", width=150)
        self.tree.column("created_at", width=120)
        self.tree.column("path", width=180)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定双击事件
        self.tree.bind('<Double-1>', self.on_item_double_click)

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="打开选中项目",
                   command=self.open_selected).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="刷新列表",
                   command=self.load_projects).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="取消",
                   command=self.dialog.destroy).pack(side=tk.LEFT)

    def load_projects(self):
        """加载项目列表"""
        try:
            # 清空现有列表
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 从数据库获取项目
            projects = self.project_controller.get_all_projects()

            if not projects:
                # 如果没有项目，显示提示
                self.tree.insert("", "end", values=("暂无项目", "请先创建新项目", "", ""))
                return

            # 添加项目到列表
            for project in projects:
                self.tree.insert("", "end", values=(
                    project.name,
                    project.description or "无描述",
                    project.created_at.strftime("%Y-%m-%d %H:%M") if project.created_at else "未知",
                    project.project_root_path or "未设置"
                ), tags=(project.id,))

        except BusinessException as e:
            messagebox.showerror("错误", e.message)
        except Exception as e:
            messagebox.showerror("错误", f"加载项目列表失败: {str(e)}")

    def on_item_double_click(self, event):
        """双击项目打开"""
        self.open_selected()

    def open_selected(self):
        """打开选中的项目"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个项目")
            return

        # 获取选中的项目ID
        item = selection[0]
        project_id = self.tree.item(item, "tags")[0]

        try:
            # 通过ID获取完整的项目信息
            self.selected_project = self.project_controller.get_project(project_id)
            self.dialog.destroy()

        except BusinessException as e:
            messagebox.showerror("错误", e.message)
        except Exception as e:
            messagebox.showerror("错误", f"打开项目失败: {str(e)}")