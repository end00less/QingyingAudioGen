# main.py
import flet as ft
from flet import ThemeMode
import sys
import os
import logging

from app.db.database import engine, Base
from app.models import *  # 导入所有模型，确保它们被注册

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入现代化主窗口
from app.ui.modern_main_window import ModernMainWindow
from app.core.app_context import AppContext


class QingyingDesktopApp:
    def __init__(self):
        logger.info("🚀 初始化清影配音软件...")

        # 初始化应用控制器
        try:
            self.app_controller = AppContext.get_instance()
            logger.info("✅ 应用控制器初始化完成")
        except Exception as e:
            logger.error(f"❌ 应用控制器初始化失败: {e}")
            raise

    def main(self, page: ft.Page):
        """Flet 应用主函数"""
        try:
            # 页面配置
            self.setup_page(page)

            # 创建并显示主窗口
            self.main_window = ModernMainWindow(page, self.app_controller)
            logger.info("✅ 主窗口创建完成")

        except Exception as e:
            logger.error(f"❌ 应用启动失败: {e}")
            self.show_error_dialog(page, f"应用启动失败: {e}")

    def setup_page(self, page: ft.Page):
        """设置页面配置"""
        page.title = "清影配音软件 v2.0"
        page.theme_mode = ThemeMode.DARK
        page.window.width = 1400
        page.window.height = 900
        page.window.min_width = 1200
        page.window.min_height = 800

        # 设置窗口图标（如果有的话）
        try:
            # 这里可以设置窗口图标
            # page.window.icon = "assets/icon.png"
            pass
        except Exception as e:
            logger.warning(f"设置窗口图标失败: {e}")

        logger.info("✅ 页面配置完成")

    def show_error_dialog(self, page: ft.Page, message: str):
        """显示错误对话框"""

        def close_dialog(e):
            page.dialog.open = False
            page.update()
            sys.exit(1)

        dialog = ft.AlertDialog(
            title=ft.Text("启动错误"),
            content=ft.Text(message),
            actions=[ft.TextButton("确定", on_click=close_dialog)],
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def run(self):
        """运行应用"""
        try:
            logger.info("🚀 启动清影配音软件...")

            # 启动 Flet 应用
            ft.app(
                target=self.main,
                name="QingyingDesktop",
                view=ft.AppView.FLET_APP
            )

        except KeyboardInterrupt:
            logger.info("👋 应用被用户中断")
        except Exception as e:
            logger.error(f"❌ 应用运行出错: {e}")
            sys.exit(1)
        finally:
            logger.info("🔚 应用退出")


def init_database():
    """初始化数据库（如果需要的话）"""
    try:


        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表初始化完成")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        return False


if __name__ == "__main__":
    # 初始化数据库
    if not init_database():
        print("数据库初始化失败，请检查配置后重试。")
        sys.exit(1)

    # 创建并运行应用
    app = QingyingDesktopApp()
    app.run()