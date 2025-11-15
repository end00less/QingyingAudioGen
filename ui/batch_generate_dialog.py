# ui/batch_generate_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from app.core.app_context import AppContext
from app.controllers.base_controller import BusinessException

class BatchGenerateDialog:
    def __init__(self, parent, chapter_id, project, app_controller):
        self.parent = parent
        self.chapter_id = chapter_id
        self.project = project
        self.app_controller = app_controller
        self.line_controller = app_controller.line_controller
        self.role_controller = app_controller.role_controller
        self.voice_controller = app_controller.voice_controller

        self.setup_dialog()
        self.load_lines()

    def setup_dialog(self):
        """设置批量生成对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("批量生成语音")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)

        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 生成选项框架
        options_frame = ttk.LabelFrame(main_frame, text="生成选项", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))

        # 生成范围
        ttk.Label(options_frame, text="生成范围:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.range_var = tk.StringVar(value="all")

        ttk.Radiobutton(options_frame, text="全部台词", variable=self.range_var, value="all").grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(options_frame, text="未生成的台词", variable=self.range_var, value="pending").grid(row=0, column=2, sticky=tk.W, pady=5)
        ttk.Radiobutton(options_frame, text="生成失败的台词", variable=self.range_var, value="failed").grid(row=0, column=3, sticky=tk.W, pady=5)

        # 并发设置
        ttk.Label(options_frame, text="并发数量:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.concurrency_var = tk.StringVar(value="1")
        concurrency_combo = ttk.Combobox(options_frame, textvariable=self.concurrency_var, width=10)
        concurrency_combo['values'] = ('1', '2', '3', '5')
        concurrency_combo.grid(row=1, column=1, sticky=tk.W, pady=5)

        # 台词列表框架
        list_frame = ttk.LabelFrame(main_frame, text="台词列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建树形视图
        columns = ('id', 'order', 'role', 'text', 'status')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        self.tree.heading('id', text='ID')
        self.tree.heading('order', text='序号')
        self.tree.heading('role', text='角色')
        self.tree.heading('text', text='台词内容')
        self.tree.heading('status', text='状态')

        self.tree.column('id', width=50)
        self.tree.column('order', width=50)
        self.tree.column('role', width=80)
        self.tree.column('text', width=300)
        self.tree.column('status', width=80)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 统计信息
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.stats_var = tk.StringVar(value="总计: 0 | 待生成: 0 | 已完成: 0 | 失败: 0")
        ttk.Label(stats_frame, textvariable=self.stats_var).pack(anchor=tk.W)

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="开始生成", command=self.start_generate).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="停止生成", command=self.stop_generate).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy).pack(side=tk.LEFT)

        self.is_generating = False
        self.generation_thread = None

    def load_lines(self):
        """通过 Controller 加载台词列表"""
        try:
            lines = self.line_controller.get_lines_by_chapter(self.chapter_id)
            self.all_lines = lines

            # 清空现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)

            for line in lines:
                role_name = self.get_role_name(line.role_id)
                self.tree.insert('', tk.END, values=(
                    line.id,
                    line.line_order or '',
                    role_name,
                    line.text_content[:50] + "..." if len(line.text_content) > 50 else line.text_content,
                    line.status or 'pending'
                ))

            self.update_stats()
        except BusinessException as e:
            messagebox.showerror("错误", e.message)

    def get_role_name(self, role_id: int) -> str:
        """获取角色名称"""
        if not role_id:
            return "旁白"
        try:
            role = self.role_controller.get_role(role_id)
            return role.name if role else "未知"
        except BusinessException:
            return "未知"

    def update_stats(self):
        """更新统计信息"""
        if not hasattr(self, 'all_lines'):
            return

        total = len(self.all_lines)
        pending = len([line for line in self.all_lines if line.status in ['pending', 'failed']])
        done = len([line for line in self.all_lines if line.status == 'done'])
        failed = len([line for line in self.all_lines if line.status == 'failed'])

        self.stats_var.set(f"总计: {total} | 待生成: {pending} | 已完成: {done} | 失败: {failed}")

    def get_lines_to_generate(self):
        """获取需要生成的台词"""
        range_type = self.range_var.get()

        if range_type == "all":
            return self.all_lines
        elif range_type == "pending":
            return [line for line in self.all_lines if line.status in ['pending', 'failed']]
        elif range_type == "failed":
            return [line for line in self.all_lines if line.status == 'failed']
        else:
            return []

    def start_generate(self):
        """开始生成"""
        lines_to_generate = self.get_lines_to_generate()
        if not lines_to_generate:
            messagebox.showwarning("警告", "没有需要生成的台词")
            return

        # 确认对话框
        if not messagebox.askyesno("确认", f"确定要批量生成 {len(lines_to_generate)} 条台词的语音吗？"):
            return

        self.is_generating = True
        self.generation_thread = threading.Thread(target=self._run_generation, args=(lines_to_generate,))
        self.generation_thread.daemon = True
        self.generation_thread.start()

    def stop_generate(self):
        """停止生成"""
        self.is_generating = False

    def _run_generation(self, lines):
        """执行批量生成"""
        try:
            total = len(lines)
            success_count = 0
            fail_count = 0

            # 创建进度对话框
            from app.core.tts_engine import TTSProgressDialog
            self.progress_dialog = TTSProgressDialog(self.dialog, "批量生成语音")

            for i, line in enumerate(lines):
                if not self.is_generating:
                    break

                # 更新进度
                progress = int((i / total) * 100)
                self.progress_dialog.update_progress(progress, f"正在生成第 {i + 1}/{total} 条台词...")

                try:
                    # 这里调用 TTS 生成逻辑
                    # 暂时模拟生成过程
                    self.line_controller.update_line(line.id, status="done")
                    success_count += 1

                except Exception as e:
                    print(f"生成台词 {line.id} 失败: {e}")
                    self.line_controller.update_line(line.id, status="failed")
                    fail_count += 1

            self.progress_dialog.close()

            # 更新界面
            self.dialog.after(0, lambda: self._on_generation_complete(success_count, fail_count))

        except Exception as e:
            if hasattr(self, 'progress_dialog'):
                self.progress_dialog.close()
            self.dialog.after(0, lambda: messagebox.showerror("错误", f"批量生成失败: {str(e)}"))

    def _on_generation_complete(self, success_count: int, fail_count: int):
        """生成完成回调"""
        self.is_generating = False
        self.load_lines()  # 刷新列表

        if fail_count == 0:
            messagebox.showinfo("成功", f"批量生成完成！\n成功: {success_count} 条")
        else:
            messagebox.showwarning("完成", f"批量生成完成！\n成功: {success_count} 条\n失败: {fail_count} 条")