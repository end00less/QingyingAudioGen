import tkinter as tk
from tkinter import ttk
import sys
import os
# 在应用启动时添加这行
from app.db.database import engine, Base
from app.models import *  # 导入所有模型，确保它们被注册

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow


class SonicValeDesktopApp:
    def __init__(self):
        # 先初始化数据库
        self.init_database()

        self.root = tk.Tk()
        self.root.title("SonicVale 配音软件 - 桌面版")
        self.root.geometry("1200x800")

        # 设置样式
        self.setup_styles()

        # 初始化主窗口
        self.main_window = MainWindow(self.root)

    def init_database(self):
        """初始化数据库表"""
        try:
            # 创建所有表
            Base.metadata.create_all(bind=engine)
            print("数据库表初始化完成")
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            # 可以选择显示错误对话框或退出应用
            tk.messagebox.showerror("数据库错误", f"数据库初始化失败: {e}")
            sys.exit(1)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        # 自定义样式
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = SonicValeDesktopApp()
    app.run()