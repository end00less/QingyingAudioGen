# ui/main_window.py
import tkinter as tk
from tkinter import ttk, messagebox
from app.core.app_context import AppContext
from app.controllers.base_controller import BusinessException


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.app_controller = AppContext.get_instance()
        self.current_project = None  # 添加当前项目状态

        self.setup_ui()
        self.load_projects()

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title_label = ttk.Label(main_frame, text="SonicVale 配音软件", style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # 项目列表框架
        list_frame = ttk.LabelFrame(main_frame, text="项目列表", padding="10")
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        # 项目列表
        self.project_listbox = tk.Listbox(list_frame, width=40, height=20)
        self.project_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.project_listbox.bind('<<ListboxSelect>>', self.on_project_select)

        # 项目操作按钮
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, pady=(10, 0))

        ttk.Button(btn_frame, text="新建项目", command=self.create_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="编辑项目", command=self.edit_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="删除项目", command=self.delete_project).pack(side=tk.LEFT)

        # 项目详情框架
        detail_frame = ttk.LabelFrame(main_frame, text="项目详情", padding="10")
        detail_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 项目详情内容
        self.detail_text = tk.Text(detail_frame, width=60, height=20, state=tk.DISABLED)
        self.detail_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 章节管理按钮
        chapter_btn_frame = ttk.Frame(detail_frame)
        chapter_btn_frame.grid(row=1, column=0, pady=(10, 0))

        ttk.Button(chapter_btn_frame, text="管理章节", command=self.manage_chapters).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(chapter_btn_frame, text="生成配音", command=self.generate_audio).pack(side=tk.LEFT)

        # 配置行列权重
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)

    def load_projects(self):
        """通过 Controller 加载项目"""
        try:
            projects = self.app_controller.project_controller.get_all_projects()
            self.project_listbox.delete(0, tk.END)
            for project in projects:
                self.project_listbox.insert(tk.END, project.name)
        except BusinessException as e:
            messagebox.showerror("错误", e.message)
        except Exception as e:
            messagebox.showerror("错误", f"系统错误: {str(e)}")

    def on_project_select(self, event):
        """当项目列表选择改变时显示项目详情"""
        selection = self.project_listbox.curselection()
        if not selection:
            return

        project_name = self.project_listbox.get(selection[0])
        try:
            projects = self.app_controller.project_controller.get_all_projects()
            project = next((p for p in projects if p.name == project_name), None)

            if project:
                self.current_project = project  # 更新当前项目
                self.show_project_details(project)
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def create_project(self):
        """通过 Controller 创建项目"""
        from app.ui.project_window import ProjectDialog
        dialog = ProjectDialog(self.root, self.app_controller.project_controller)

        # 等待对话框关闭
        self.root.wait_window(dialog.dialog)

        if dialog.result:  # 这里 dialog.result 就是 Project Entity 对象
            # 刷新项目列表
            self.load_projects()

            # 自动选中新建的项目
            self.select_project_by_id(dialog.result.id)

            # 设置当前项目
            self.current_project = dialog.result

            print(f"新建项目成功，项目ID: {dialog.result.id}, 名称: {dialog.result.name}")

    def edit_project(self):
        """通过 Controller 编辑项目"""
        selection = self.project_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个项目")
            return

        project_name = self.project_listbox.get(selection[0])
        try:
            # 通过名称查找项目
            projects = self.app_controller.project_controller.get_all_projects()
            project = next((p for p in projects if p.name == project_name), None)

            if project:
                from app.ui.project_window import ProjectDialog
                dialog = ProjectDialog(self.root, self.app_controller.project_controller, project)
                if dialog.result:
                    self.load_projects()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def delete_project(self):
        """通过 Controller 删除项目"""
        selection = self.project_listbox.curselection()
        if not selection:
            return

        project_name = self.project_listbox.get(selection[0])

        try:
            projects = self.app_controller.project_controller.get_all_projects()
            project = next((p for p in projects if p.name == project_name), None)

            if project and messagebox.askyesno("确认删除", f"确定要删除项目 '{project_name}' 吗？"):
                self.app_controller.project_controller.delete_project(project.id)
                messagebox.showinfo("成功", "项目删除成功")
                self.load_projects()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def manage_chapters(self):
        """通过 Controller 管理章节"""
        selection = self.project_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个项目")
            return

        project_name = self.project_listbox.get(selection[0])
        try:
            projects = self.app_controller.project_controller.get_all_projects()
            project = next((p for p in projects if p.name == project_name), None)

            if project:
                from app.ui.chapter_window import ChapterWindow
                chapter_window = ChapterWindow(self.root, project, self.app_controller)
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def generate_audio(self):
        """生成项目配音"""
        selection = self.project_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个项目")
            return

        project_name = self.project_listbox.get(selection[0])
        try:
            # 通过名称查找项目
            projects = self.app_controller.project_controller.get_all_projects()
            project = next((p for p in projects if p.name == project_name), None)

            if project:
                # 确认生成
                if not messagebox.askyesno("确认生成", f"确定要为项目 '{project_name}' 生成配音吗？"):
                    return

                # 调用控制器生成配音
                result = self.app_controller.audio_generation_controller.generate_project_audio(project.id)

                if result.success:
                    messagebox.showinfo("成功", f"配音生成完成！\n生成文件数量: {result.generated_files}\n保存路径: {result.output_path}")
                else:
                    messagebox.showerror("生成失败", f"配音生成过程中出现错误: {result.error_message}")

        except BusinessException as e:
            messagebox.showerror("错误", e.message)
        except Exception as e:
            messagebox.showerror("错误", f"系统错误: {str(e)}")

    def show_project_details(self, project):
        """显示项目详情"""
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)

        details = f"""项目名称: {project.name}
描述: {project.description or '无'}
LLM模型: {project.llm_model or '未设置'}
TTS服务: {project.tts_provider_id or '未设置'}
精准填充: {'是' if project.is_precise_fill else '否'}
项目路径: {project.project_root_path or '未设置'}
创建时间: {project.created_at}
"""
        self.detail_text.insert(1.0, details)
        self.detail_text.config(state=tk.DISABLED)