# ui/audio_window.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
from app.core.app_context import AppContext
from app.controllers.base_controller import BusinessException

class AudioEditorWindow:
    def __init__(self, parent, audio_path: str):
        self.parent = parent
        self.audio_path = audio_path

        self.setup_window()
        self.load_audio()

    def setup_window(self):
        """设置窗口界面"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("音频编辑器")
        self.window.geometry("600x500")
        self.window.transient(self.parent)

        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        main_frame = ttk.Frame(self.window, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 音频信息显示
        info_frame = ttk.LabelFrame(main_frame, text="音频信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        self.info_text = tk.Text(info_frame, height=4, width=60, state=tk.DISABLED)
        self.info_text.pack(fill=tk.X)

        # 播放控制
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(control_frame, text="播放", command=self.play_audio).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="停止", command=self.stop_audio).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="刷新信息", command=self.load_audio).pack(side=tk.LEFT)

        # 音频编辑功能
        edit_frame = ttk.LabelFrame(main_frame, text="音频编辑", padding="10")
        edit_frame.pack(fill=tk.BOTH, expand=True)

        # 剪切功能
        cut_frame = ttk.Frame(edit_frame)
        cut_frame.pack(fill=tk.X, pady=5)

        ttk.Label(cut_frame, text="剪切区间:").grid(row=0, column=0, sticky=tk.W)
        self.start_var = tk.StringVar(value="0")
        self.end_var = tk.StringVar(value="1000")

        ttk.Entry(cut_frame, textvariable=self.start_var, width=8).grid(row=0, column=1, padx=(5, 10))
        ttk.Label(cut_frame, text="ms 到").grid(row=0, column=2)
        ttk.Entry(cut_frame, textvariable=self.end_var, width=8).grid(row=0, column=3, padx=(5, 10))
        ttk.Label(cut_frame, text="ms").grid(row=0, column=4)
        ttk.Button(cut_frame, text="剪切", command=self.cut_audio).grid(row=0, column=5, padx=(10, 0))

        # 变速变调
        speed_frame = ttk.Frame(edit_frame)
        speed_frame.pack(fill=tk.X, pady=5)

        ttk.Label(speed_frame, text="变速:").grid(row=0, column=0, sticky=tk.W)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, from_=0.5, to=2.0, variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.grid(row=0, column=1, padx=(5, 10), sticky=tk.EW)
        ttk.Label(speed_frame, textvariable=self.speed_var).grid(row=0, column=2)
        ttk.Button(speed_frame, text="应用", command=self.change_speed).grid(row=0, column=3, padx=(10, 0))

        # 音量调整
        volume_frame = ttk.Frame(edit_frame)
        volume_frame.pack(fill=tk.X, pady=5)

        ttk.Label(volume_frame, text="音量:").grid(row=0, column=0, sticky=tk.W)
        self.volume_var = tk.DoubleVar(value=1.0)
        volume_scale = ttk.Scale(volume_frame, from_=0.0, to=2.0, variable=self.volume_var, orient=tk.HORIZONTAL)
        volume_scale.grid(row=0, column=1, padx=(5, 10), sticky=tk.EW)
        ttk.Label(volume_frame, textvariable=self.volume_var).grid(row=0, column=2)
        ttk.Button(volume_frame, text="应用", command=self.change_volume).grid(row=0, column=3, padx=(10, 0))

        # 配置权重
        speed_frame.columnconfigure(1, weight=1)
        volume_frame.columnconfigure(1, weight=1)
        edit_frame.columnconfigure(0, weight=1)

    def load_audio(self):
        """加载音频文件"""
        try:
            if not os.path.exists(self.audio_path):
                messagebox.showerror("错误", "音频文件不存在")
                self.window.destroy()
                return

            # 这里调用音频信息获取逻辑
            from core.audio_engine import AudioProcessor
            audio_processor = AudioProcessor(self.audio_path)
            audio_info = audio_processor.get_audio_info()

            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)

            info_str = f"""文件路径: {self.audio_path}
时长: {audio_info.get('duration', 0)} 秒
采样率: {audio_info.get('sample_rate', 0)} Hz
声道数: {audio_info.get('channels', 0)}
格式: {audio_info.get('format', '未知')}
"""
            self.info_text.insert(1.0, info_str)
            self.info_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("错误", f"加载音频失败: {str(e)}")

    def play_audio(self):
        """播放音频"""
        try:
            from core.audio_engine import AudioPlayer
            audio_player = AudioPlayer()
            if audio_player.play_audio(self.audio_path):
                messagebox.showinfo("提示", "音频开始播放")
            else:
                messagebox.showerror("错误", "播放失败")
        except Exception as e:
            messagebox.showerror("错误", f"播放失败: {str(e)}")

    def stop_audio(self):
        """停止播放"""
        try:
            from core.audio_engine import AudioPlayer
            audio_player = AudioPlayer()
            audio_player.stop_audio()
        except Exception as e:
            messagebox.showerror("错误", f"停止播放失败: {str(e)}")

    def cut_audio(self):
        """剪切音频"""
        try:
            start_ms = int(self.start_var.get())
            end_ms = int(self.end_var.get())

            if start_ms >= end_ms:
                messagebox.showwarning("警告", "开始时间必须小于结束时间")
                return

            from core.audio_engine import AudioProcessor
            audio_processor = AudioProcessor(self.audio_path)
            audio_processor.cut(start_ms, end_ms)
            messagebox.showinfo("成功", "音频剪切完成")
            self.load_audio()  # 刷新信息

        except ValueError:
            messagebox.showerror("错误", "请输入有效的时间数值")
        except Exception as e:
            messagebox.showerror("错误", f"剪切失败: {str(e)}")

    def change_speed(self):
        """改变速度"""
        try:
            speed = self.speed_var.get()
            from core.audio_engine import AudioProcessor
            audio_processor = AudioProcessor(self.audio_path)
            audio_processor.change_speed(speed)
            messagebox.showinfo("成功", "速度调整完成")
            self.load_audio()
        except Exception as e:
            messagebox.showerror("错误", f"速度调整失败: {str(e)}")

    def change_volume(self):
        """调整音量"""
        try:
            volume = self.volume_var.get()
            from core.audio_engine import AudioProcessor
            audio_processor = AudioProcessor(self.audio_path)
            audio_processor.change_volume(volume)
            messagebox.showinfo("成功", "音量调整完成")
        except Exception as e:
            messagebox.showerror("错误", f"音量调整失败: {str(e)}")