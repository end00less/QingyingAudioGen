# ui/style_config.py
import tkinter as tk
from tkinter import ttk


class UIStyles:
    """UI样式配置类"""

    # 颜色配置
    COLORS = {
        'primary': '#007bff',  # 主色调 - 蓝色
        'secondary': '#6c757d',  # 次要色 - 灰色
        'success': '#28a745',  # 成功色 - 绿色
        'warning': '#ffc107',  # 警告色 - 黄色
        'danger': '#dc3545',  # 危险色 - 红色
        'light': '#f8f9fa',  # 浅色
        'dark': '#343a40',  # 深色
        'muted': '#6c757d',  # 静音色
        'white': '#ffffff',  # 白色
        'background': '#f5f5f5',  # 背景色
        'card_bg': '#ffffff',  # 卡片背景
        'border': '#dee2e6',  # 边框色
        'input_bg': '#ffffff',  # 输入框背景
        'hover': '#e9ecef',  # 悬停色
        'active': '#dee2e6',  # 激活色
    }

    # 字体配置
    FONTS = {
        'title': ('Microsoft YaHei', 24, 'bold'),
        'subtitle': ('Microsoft YaHei', 16, 'normal'),
        'heading': ('Microsoft YaHei', 14, 'bold'),
        'body': ('Microsoft YaHei', 12, 'normal'),
        'small': ('Microsoft YaHei', 10, 'normal'),
        'button': ('Microsoft YaHei', 11, 'normal'),
        'input': ('Microsoft YaHei', 11, 'normal'),
        'muted': ('Microsoft YaHei', 11, 'normal'),
    }

    # 间距配置
    SPACING = {
        'xs': 4,
        'sm': 8,
        'md': 16,
        'lg': 24,
        'xl': 32,
        'xxl': 48,
    }

    # 按钮样式配置
    BUTTON_STYLES = {
        'primary': {
            'bg': COLORS['primary'],
            'fg': COLORS['white'],
            'hover_bg': '#0056b3',
            'active_bg': '#004085',
        },
        'secondary': {
            'bg': COLORS['secondary'],
            'fg': COLORS['white'],
            'hover_bg': '#545b62',
            'active_bg': '#3d4142',
        },
        'outline': {
            'bg': COLORS['white'],
            'fg': COLORS['primary'],
            'hover_bg': COLORS['hover'],
            'active_bg': COLORS['active'],
            'border': COLORS['primary'],
        },
        'success': {
            'bg': COLORS['success'],
            'fg': COLORS['white'],
            'hover_bg': '#1e7e34',
            'active_bg': '#155724',
        },
        'danger': {
            'bg': COLORS['danger'],
            'fg': COLORS['white'],
            'hover_bg': '#c82333',
            'active_bg': '#a71e2a',
        }
    }


class StyleHelper:
    """样式辅助类"""

    @staticmethod
    def create_styled_frame(parent, style_type='flat'):
        """创建样式化框架"""
        frame = tk.Frame(parent)

        if style_type == 'card':
            frame.configure(
                bg=UIStyles.COLORS['card_bg'],
                relief=tk.RAISED,
                bd=1
            )
        elif style_type == 'flat':
            frame.configure(
                bg=UIStyles.COLORS['background'],
                relief=tk.FLAT,
                bd=0
            )
        else:  # default
            frame.configure(
                bg=UIStyles.COLORS['white'],
                relief=tk.FLAT,
                bd=0
            )

        return frame

    @staticmethod
    def create_styled_label(parent, text, style='body', textvariable=None):
        """创建样式化标签"""
        font = UIStyles.FONTS.get(style, UIStyles.FONTS['body'])
        fg_color = UIStyles.COLORS.get('dark')

        if style == 'title':
            fg_color = UIStyles.COLORS['dark']
        elif style == 'subtitle':
            fg_color = UIStyles.COLORS['muted']
        elif style == 'heading':
            fg_color = UIStyles.COLORS['dark']
        elif style == 'muted':
            fg_color = UIStyles.COLORS['muted']
        elif style == 'primary':
            fg_color = UIStyles.COLORS['primary']

        label = tk.Label(
            parent,
            text=text,
            font=font,
            fg=fg_color,
            bg=UIStyles.COLORS['background'] if parent.cget('bg') == UIStyles.COLORS['background'] else UIStyles.COLORS[
                'card_bg'],
            textvariable=textvariable
        )

        return label

    @staticmethod
    def create_styled_button(parent, text, style_type='primary', size='normal', command=None):
        """创建样式化按钮"""
        style_config = UIStyles.BUTTON_STYLES.get(style_type, UIStyles.BUTTON_STYLES['primary'])

        # 根据大小设置padding
        if size == 'large':
            padx = UIStyles.SPACING['lg']
            pady = UIStyles.SPACING['md']
        elif size == 'small':
            padx = UIStyles.SPACING['sm']
            pady = UIStyles.SPACING['xs']
        else:  # normal
            padx = UIStyles.SPACING['md']
            pady = UIStyles.SPACING['sm']

        button = tk.Button(
            parent,
            text=text,
            font=UIStyles.FONTS['button'],
            bg=style_config['bg'],
            fg=style_config['fg'],
            relief=tk.FLAT,
            bd=0,
            padx=padx,
            pady=pady,
            cursor='hand2',
            command=command
        )

        # 添加悬停效果
        def on_enter(e):
            button.configure(bg=style_config['hover_bg'])

        def on_leave(e):
            button.configure(bg=style_config['bg'])

        def on_click(e):
            button.configure(bg=style_config['active_bg'])

        def on_release(e):
            button.configure(bg=style_config['hover_bg'])

        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)
        button.bind('<Button-1>', on_click)
        button.bind('<ButtonRelease-1>', on_release)

        # 如果是outline样式，添加边框
        if style_type == 'outline' and 'border' in style_config:
            button.configure(
                relief=tk.SOLID,
                bd=1,
                highlightbackground=style_config['border'],
                highlightcolor=style_config['border']
            )

        return button

    @staticmethod
    def create_styled_entry(parent, textvariable=None, width=20):
        """创建样式化输入框"""
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            font=UIStyles.FONTS['input'],
            bg=UIStyles.COLORS['input_bg'],
            fg=UIStyles.COLORS['dark'],
            relief=tk.SOLID,
            bd=1,
            insertbackground=UIStyles.COLORS['primary'],
            width=width
        )

        return entry

    @staticmethod
    def create_styled_combobox(parent, textvariable=None, values=None, width=20, state='readonly'):
        """创建样式化下拉框"""
        combo = ttk.Combobox(
            parent,
            textvariable=textvariable,
            values=values or [],
            width=width,
            state=state,
            font=UIStyles.FONTS['input']
        )

        return combo
