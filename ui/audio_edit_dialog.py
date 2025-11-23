# app/ui/audio_edit_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
from app.dto.line_dto import LineAudioProcessDTO


class AudioEditDialog:
    def __init__(self, parent, line_controller, line_id):
        self.parent = parent
        self.line_controller = line_controller
        self.line_id = line_id
        self.line = None
        self.audio_duration = 0  # 音频总时长（毫秒）

        self.setup_dialog()
        self.load_line_data()

    def setup_dialog(self):
        """设置对话框界面"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("音频编辑 - 任意位置裁剪")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        # 主框架
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 音频信息
        info_frame = ttk.LabelFrame(main_frame, text="音频信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(info_frame, text="台词内容:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.content_var = tk.StringVar()
        content_label = ttk.Label(info_frame, textvariable=self.content_var, wraplength=500)
        content_label.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(info_frame, text="音频文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.audio_path_var = tk.StringVar()
        audio_label = ttk.Label(info_frame, textvariable=self.audio_path_var, wraplength=500)
        audio_label.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(info_frame, text="音频时长:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.duration_var = tk.StringVar(value="计算中...")
        duration_label = ttk.Label(info_frame, textvariable=self.duration_var)
        duration_label.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))

        # 精确裁剪设置
        crop_frame = ttk.LabelFrame(main_frame, text="精确裁剪", padding="10")
        crop_frame.pack(fill=tk.X, pady=(0, 10))

        # 裁剪模式选择
        ttk.Label(crop_frame, text="裁剪模式:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.crop_mode_var = tk.StringVar(value="delete")
        mode_frame = ttk.Frame(crop_frame)
        mode_frame.grid(row=0, column=1, columnspan=3, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Radiobutton(mode_frame, text="删除选定区间", variable=self.crop_mode_var,
                        value="delete", command=self.on_crop_mode_change).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="保留选定区间", variable=self.crop_mode_var,
                        value="keep", command=self.on_crop_mode_change).pack(side=tk.LEFT, padx=(20, 0))

        # 时间区间设置
        time_frame = ttk.Frame(crop_frame)
        time_frame.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(time_frame, text="开始时间:").pack(side=tk.LEFT)
        self.start_ms_var = tk.StringVar()
        self.start_entry = ttk.Entry(time_frame, textvariable=self.start_ms_var, width=8)
        self.start_entry.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(time_frame, text="结束时间:").pack(side=tk.LEFT)
        self.end_ms_var = tk.StringVar()
        self.end_entry = ttk.Entry(time_frame, textvariable=self.end_ms_var, width=8)
        self.end_entry.pack(side=tk.LEFT, padx=(5, 15))

        ttk.Label(time_frame, text="毫秒").pack(side=tk.LEFT)

        # 快速时间按钮
        quick_buttons_frame = ttk.Frame(crop_frame)
        quick_buttons_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Button(quick_buttons_frame, text="设置开头", command=lambda: self.set_quick_time("start", 0)).pack(side=tk.LEFT,
                                                                                                           padx=(0, 5))
        ttk.Button(quick_buttons_frame, text="设置中间", command=lambda: self.set_quick_time("middle")).pack(side=tk.LEFT,
                                                                                                         padx=(0, 5))
        ttk.Button(quick_buttons_frame, text="设置结尾", command=lambda: self.set_quick_time("end")).pack(side=tk.LEFT,
                                                                                                      padx=(0, 5))
        ttk.Button(quick_buttons_frame, text="交换区间", command=self.swap_times).pack(side=tk.LEFT, padx=(0, 5))

        # 裁剪说明
        self.crop_info_var = tk.StringVar()
        crop_info_label = ttk.Label(crop_frame, textvariable=self.crop_info_var, foreground="blue")
        crop_info_label.grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=5, padx=(10, 0))

        # 音频处理选项
        process_frame = ttk.LabelFrame(main_frame, text="音频处理", padding="10")
        process_frame.pack(fill=tk.X, pady=(0, 10))

        # 变速控制
        ttk.Label(process_frame, text="播放速度:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(process_frame, from_=0.5, to=2.0, variable=self.speed_var,
                                orient=tk.HORIZONTAL, length=200)
        speed_scale.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.speed_label = ttk.Label(process_frame, text="1.0x")
        self.speed_label.grid(row=0, column=2, sticky=tk.W, pady=5, padx=(10, 0))

        # 音量控制
        ttk.Label(process_frame, text="音量:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.volume_var = tk.DoubleVar(value=1.0)
        volume_scale = ttk.Scale(process_frame, from_=0.0, to=2.0, variable=self.volume_var,
                                 orient=tk.HORIZONTAL, length=200)
        volume_scale.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.volume_label = ttk.Label(process_frame, text="100%")
        self.volume_label.grid(row=1, column=2, sticky=tk.W, pady=5, padx=(10, 0))

        # 静音设置
        ttk.Label(process_frame, text="末尾静音 (秒):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.silence_var = tk.DoubleVar(value=0.0)
        silence_spin = ttk.Spinbox(process_frame, from_=-5.0, to=10.0, increment=0.1,
                                   textvariable=self.silence_var, width=8)
        silence_spin.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Label(process_frame, text="正数:添加静音, 负数:裁剪末尾").grid(row=2, column=2, sticky=tk.W, pady=5, padx=(10, 0))

        # 当前时间点插入静音
        ttk.Label(process_frame, text="当前位置插入静音:").grid(row=3, column=0, sticky=tk.W, pady=5)
        insert_frame = ttk.Frame(process_frame)
        insert_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5, padx=(10, 0))

        ttk.Label(insert_frame, text="位置(ms):").pack(side=tk.LEFT)
        self.current_ms_var = tk.StringVar()
        current_entry = ttk.Entry(insert_frame, textvariable=self.current_ms_var, width=8)
        current_entry.pack(side=tk.LEFT, padx=(5, 10))

        ttk.Label(insert_frame, text="时长(s):").pack(side=tk.LEFT)
        self.insert_silence_var = tk.DoubleVar(value=1.0)
        insert_spin = ttk.Spinbox(insert_frame, from_=0.1, to=10.0, increment=0.1,
                                  textvariable=self.insert_silence_var, width=6)
        insert_spin.pack(side=tk.LEFT, padx=(5, 0))

        # 预览和操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame, text="播放原音频", command=self.play_original, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="播放选区", command=self.play_selection, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="预览效果", command=self.preview_audio, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="应用处理", command=self.apply_processing, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="重置", command=self.reset_values, width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy, width=12).pack(side=tk.LEFT)

        # 绑定事件
        speed_scale.configure(command=self.on_speed_change)
        volume_scale.configure(command=self.on_volume_change)
        self.start_entry.bind('<KeyRelease>', self.on_time_change)
        self.end_entry.bind('<KeyRelease>', self.on_time_change)

        # 初始化裁剪信息
        self.on_crop_mode_change()

    def load_line_data(self):
        """加载台词数据"""
        try:
            self.line = self.line_controller.get_line(self.line_id)
            if self.line:
                self.content_var.set(self.line.text_content[:100] + "..." if len(
                    self.line.text_content) > 100 else self.line.text_content)
                self.audio_path_var.set(os.path.basename(self.line.audio_path) if self.line.audio_path else "无音频文件")

                # 获取音频时长
                if self.line.audio_path and os.path.exists(self.line.audio_path):
                    self.audio_duration = self.get_audio_duration(self.line.audio_path)
                    duration_sec = self.audio_duration / 1000.0
                    self.duration_var.set(f"{duration_sec:.2f} 秒 ({self.audio_duration} 毫秒)")
                else:
                    self.duration_var.set("无法获取时长")
            else:
                messagebox.showerror("错误", "台词不存在")
                self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"加载台词失败: {str(e)}")
            self.dialog.destroy()

    def get_audio_duration(self, audio_path):
        """获取音频时长（毫秒）"""
        try:
            import soundfile as sf
            info = sf.info(audio_path)
            return int(info.duration * 1000)  # 转换为毫秒
        except:
            try:
                import wave
                with wave.open(audio_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    return int(frames / float(rate) * 1000)
            except:
                return 0

    def on_crop_mode_change(self):
        """裁剪模式变化回调"""
        mode = self.crop_mode_var.get()
        if mode == "delete":
            self.crop_info_var.set("将删除选定时间区间的内容，保留前后部分")
        else:
            self.crop_info_var.set("将保留选定时间区间的内容，删除其他部分")

    def on_speed_change(self, value):
        """速度变化回调"""
        speed = float(value)
        self.speed_label.config(text=f"{speed:.1f}x")

    def on_volume_change(self, value):
        """音量变化回调"""
        volume = float(value)
        self.volume_label.config(text=f"{int(volume * 100)}%")

    def on_time_change(self, event=None):
        """时间输入变化回调"""
        # 可以在这里添加时间验证逻辑
        pass

    def set_quick_time(self, position, specific_time=None):
        """设置快速时间"""
        if self.audio_duration == 0:
            messagebox.showwarning("警告", "无法获取音频时长")
            return

        if position == "start":
            time_val = 0
        elif position == "end":
            time_val = self.audio_duration
        elif position == "middle":
            time_val = self.audio_duration // 2
        elif specific_time is not None:
            time_val = specific_time
        else:
            return

        # 交替设置开始和结束时间
        if not self.start_ms_var.get():
            self.start_ms_var.set(str(time_val))
        elif not self.end_ms_var.get():
            self.end_ms_var.set(str(time_val))
        else:
            # 如果都已设置，询问用户要设置哪个
            self.start_ms_var.set(str(time_val))

    def swap_times(self):
        """交换开始和结束时间"""
        start_val = self.start_ms_var.get()
        end_val = self.end_ms_var.get()
        self.start_ms_var.set(end_val)
        self.end_ms_var.set(start_val)

    def play_original(self):
        """播放原音频"""
        if not self.line or not self.line.audio_path:
            messagebox.showwarning("警告", "音频文件不存在")
            return

        from app.services.audio_player_service import audio_player
        audio_player.play_audio(self.line.audio_path)

    def play_selection(self):
        """播放选定的时间区间"""
        if not self.line or not self.line.audio_path:
            messagebox.showwarning("警告", "音频文件不存在")
            return

        try:
            start_ms = int(self.start_ms_var.get()) if self.start_ms_var.get() else 0
            end_ms = int(self.end_ms_var.get()) if self.end_ms_var.get() else self.audio_duration

            if start_ms >= end_ms:
                messagebox.showwarning("警告", "开始时间必须小于结束时间")
                return

            # 使用ffmpeg裁剪并播放选定区间
            import tempfile
            import subprocess

            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"selection_{self.line_id}.wav")

            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', self.line.audio_path,
                '-ss', str(start_ms / 1000.0),
                '-to', str(end_ms / 1000.0),
                '-c', 'copy', temp_path
            ]

            # 执行ffmpeg命令
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)

            if os.path.exists(temp_path):
                from app.services.audio_player_service import audio_player
                audio_player.play_audio(temp_path)
                messagebox.showinfo("提示", f"正在播放选定区间: {start_ms}-{end_ms}ms")
            else:
                messagebox.showerror("错误", "选区播放失败")

        except ValueError:
            messagebox.showwarning("警告", "请输入有效的时间数字")
        except Exception as e:
            messagebox.showerror("错误", f"播放选区失败: {str(e)}")

    def preview_audio(self):
        """预览音频效果"""
        if not self.validate_inputs():
            return

        try:
            # 创建临时文件用于预览
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"preview_{self.line_id}.wav")

            # 构建处理参数
            dto = self.create_audio_dto()

            # 使用line_service处理音频到临时文件
            success = self.line_controller.line_service.process_audio_ffmpeg_cut(
                audio_path=self.line.audio_path,
                speed=dto.speed,
                volume=dto.volume,
                start_ms=dto.start_ms,
                end_ms=dto.end_ms,
                silence_sec=dto.silence_sec,
                out_path=temp_path
            )

            if success and os.path.exists(temp_path):
                # 使用音频播放器播放预览
                from app.services.audio_player_service import audio_player
                audio_player.play_audio(temp_path)
                messagebox.showinfo("提示", "正在播放预览音频")
            else:
                messagebox.showerror("错误", "预览生成失败")

        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {str(e)}")

    def apply_processing(self):
        """应用音频处理"""
        if not self.validate_inputs():
            return

        try:
            # 构建处理参数
            dto = self.create_audio_dto()

            # 调用line_service处理音频
            success = self.line_controller.line_service.process_audio(self.line_id, dto)

            if success:
                messagebox.showinfo("成功", "音频处理完成")
                self.dialog.destroy()
            else:
                messagebox.showerror("错误", "音频处理失败")

        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")

    def validate_inputs(self):
        """验证输入参数"""
        if not self.line or not self.line.audio_path:
            messagebox.showwarning("警告", "音频文件不存在")
            return False

        # 验证裁剪时间
        try:
            start_ms = int(self.start_ms_var.get()) if self.start_ms_var.get() else None
            end_ms = int(self.end_ms_var.get()) if self.end_ms_var.get() else None

            if start_ms is not None and end_ms is not None:
                if start_ms >= end_ms:
                    messagebox.showwarning("警告", "开始时间必须小于结束时间")
                    return False
                if end_ms > self.audio_duration:
                    messagebox.showwarning("警告", f"结束时间不能超过音频总时长 {self.audio_duration}ms")
                    return False

        except ValueError:
            messagebox.showwarning("警告", "裁剪时间必须是数字")
            return False

        return True

    def create_audio_dto(self):
        """创建音频处理DTO"""
        # 解析参数
        speed = self.speed_var.get()
        volume = self.volume_var.get()
        silence_sec = self.silence_var.get()
        crop_mode = self.crop_mode_var.get()

        # 解析裁剪时间
        start_ms = None
        end_ms = None
        try:
            if self.start_ms_var.get():
                start_ms = int(self.start_ms_var.get())
            if self.end_ms_var.get():
                end_ms = int(self.end_ms_var.get())
        except ValueError:
            pass

        # 解析插入静音参数
        current_ms = None
        insert_silence = None
        try:
            if self.current_ms_var.get():
                current_ms = int(self.current_ms_var.get())
                insert_silence = self.insert_silence_var.get()
        except ValueError:
            pass

        return LineAudioProcessDTO(
            speed=speed,
            volume=volume,
            start_ms=start_ms,
            end_ms=end_ms,
            silence_sec=silence_sec,
            current_ms=current_ms,
            crop_mode=crop_mode
        )

    def reset_values(self):
        """重置所有值为默认"""
        self.speed_var.set(1.0)
        self.volume_var.set(1.0)
        self.start_ms_var.set("")
        self.end_ms_var.set("")
        self.silence_var.set(0.0)
        self.current_ms_var.set("")
        self.insert_silence_var.set(1.0)
        self.crop_mode_var.set("delete")
        self.speed_label.config(text="1.0x")
        self.volume_label.config(text="100%")
        self.on_crop_mode_change()