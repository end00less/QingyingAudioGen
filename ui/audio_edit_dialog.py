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
        self.dialog.geometry("800x900")  # 进一步增大窗口尺寸
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)

        # 创建主框架，不使用滚动条
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 音频信息
        info_frame = ttk.LabelFrame(main_frame, text="音频信息", padding="15")
        info_frame.pack(fill=tk.X, pady=(0, 15))

        # 使用网格布局
        ttk.Label(info_frame, text="台词内容:").grid(row=0, column=0, sticky=tk.W, pady=8)
        self.content_var = tk.StringVar()
        content_label = ttk.Label(info_frame, textvariable=self.content_var, wraplength=650)
        content_label.grid(row=0, column=1, columnspan=3, sticky=tk.W + tk.E, pady=8, padx=(15, 0))

        ttk.Label(info_frame, text="音频文件:").grid(row=1, column=0, sticky=tk.W, pady=8)
        self.audio_path_var = tk.StringVar()
        audio_label = ttk.Label(info_frame, textvariable=self.audio_path_var, wraplength=650)
        audio_label.grid(row=1, column=1, columnspan=3, sticky=tk.W + tk.E, pady=8, padx=(15, 0))

        ttk.Label(info_frame, text="音频时长:").grid(row=2, column=0, sticky=tk.W, pady=8)
        self.duration_var = tk.StringVar(value="计算中...")
        duration_label = ttk.Label(info_frame, textvariable=self.duration_var)
        duration_label.grid(row=2, column=1, sticky=tk.W, pady=8, padx=(15, 0))

        # 精确裁剪设置
        crop_frame = ttk.LabelFrame(main_frame, text="精确裁剪设置", padding="15")
        crop_frame.pack(fill=tk.X, pady=(0, 15))

        # 裁剪模式选择
        ttk.Label(crop_frame, text="裁剪模式:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.crop_mode_var = tk.StringVar(value="delete")
        mode_frame = ttk.Frame(crop_frame)
        mode_frame.grid(row=0, column=1, columnspan=3, sticky=tk.W, pady=10, padx=(15, 0))
        ttk.Radiobutton(mode_frame, text="删除选定区间", variable=self.crop_mode_var,
                        value="delete", command=self.on_crop_mode_change).pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="保留选定区间", variable=self.crop_mode_var,
                        value="keep", command=self.on_crop_mode_change).pack(side=tk.LEFT, padx=(25, 0))

        # 时间区间设置
        ttk.Label(crop_frame, text="时间区间:").grid(row=1, column=0, sticky=tk.W, pady=10)
        time_frame = ttk.Frame(crop_frame)
        time_frame.grid(row=1, column=1, columnspan=3, sticky=tk.W, pady=10, padx=(15, 0))

        ttk.Label(time_frame, text="开始时间:").pack(side=tk.LEFT)
        self.start_ms_var = tk.StringVar()
        self.start_entry = ttk.Entry(time_frame, textvariable=self.start_ms_var, width=12)
        self.start_entry.pack(side=tk.LEFT, padx=(8, 20))

        ttk.Label(time_frame, text="结束时间:").pack(side=tk.LEFT)
        self.end_ms_var = tk.StringVar()
        self.end_entry = ttk.Entry(time_frame, textvariable=self.end_ms_var, width=12)
        self.end_entry.pack(side=tk.LEFT, padx=(8, 15))

        ttk.Label(time_frame, text="毫秒").pack(side=tk.LEFT)

        # 快速时间按钮
        ttk.Label(crop_frame, text="快速设置:").grid(row=2, column=0, sticky=tk.W, pady=10)
        quick_buttons_frame = ttk.Frame(crop_frame)
        quick_buttons_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=10, padx=(15, 0))

        ttk.Button(quick_buttons_frame, text="设置开头", command=lambda: self.set_quick_time("start", 0),
                   width=12).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(quick_buttons_frame, text="设置中间", command=lambda: self.set_quick_time("middle"),
                   width=12).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(quick_buttons_frame, text="设置结尾", command=lambda: self.set_quick_time("end"),
                   width=12).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(quick_buttons_frame, text="交换区间", command=self.swap_times,
                   width=12).pack(side=tk.LEFT, padx=(0, 8))

        # 裁剪说明
        self.crop_info_var = tk.StringVar()
        crop_info_label = ttk.Label(crop_frame, textvariable=self.crop_info_var,
                                    foreground="blue")
        crop_info_label.grid(row=3, column=0, columnspan=4, sticky=tk.W + tk.E, pady=10, padx=(0, 0))

        # 音频处理选项
        process_frame = ttk.LabelFrame(main_frame, text="音频处理选项", padding="15")
        process_frame.pack(fill=tk.X, pady=(0, 15))

        # 变速控制 - 修复滑块问题
        ttk.Label(process_frame, text="播放速度:").grid(row=0, column=0, sticky=tk.W, pady=12)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_frame = ttk.Frame(process_frame)
        speed_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W + tk.E, pady=12, padx=(15, 0))

        # 修复：使用正常的Scale而不是ttk.Scale
        self.speed_scale = tk.Scale(speed_frame, from_=0.5, to=2.0, variable=self.speed_var,
                                    orient=tk.HORIZONTAL, length=350, resolution=0.1,
                                    showvalue=False, command=self.on_speed_change)
        self.speed_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.speed_label = ttk.Label(speed_frame, text="1.0x", width=6)
        self.speed_label.pack(side=tk.LEFT, padx=(15, 0))

        # 音量控制 - 修复滑块问题
        ttk.Label(process_frame, text="音量调节:").grid(row=1, column=0, sticky=tk.W, pady=12)
        self.volume_var = tk.DoubleVar(value=1.0)
        volume_frame = ttk.Frame(process_frame)
        volume_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W + tk.E, pady=12, padx=(15, 0))

        # 修复：使用正常的Scale而不是ttk.Scale
        self.volume_scale = tk.Scale(volume_frame, from_=0.0, to=2.0, variable=self.volume_var,
                                     orient=tk.HORIZONTAL, length=350, resolution=0.1,
                                     showvalue=False, command=self.on_volume_change)
        self.volume_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.volume_label = ttk.Label(volume_frame, text="100%", width=6)
        self.volume_label.pack(side=tk.LEFT, padx=(15, 0))

        # 静音设置
        ttk.Label(process_frame, text="末尾处理:").grid(row=2, column=0, sticky=tk.W, pady=12)
        silence_frame = ttk.Frame(process_frame)
        silence_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=12, padx=(15, 0))

        ttk.Label(silence_frame, text="静音时长:").pack(side=tk.LEFT)
        self.silence_var = tk.DoubleVar(value=0.0)
        silence_spin = ttk.Spinbox(silence_frame, from_=-5.0, to=10.0, increment=0.1,
                                   textvariable=self.silence_var, width=8)
        silence_spin.pack(side=tk.LEFT, padx=(8, 15))
        ttk.Label(silence_frame, text="秒 (正数:添加静音, 负数:裁剪末尾)").pack(side=tk.LEFT)

        # 当前时间点插入静音
        ttk.Label(process_frame, text="插入静音:").grid(row=3, column=0, sticky=tk.W, pady=12)
        insert_frame = ttk.Frame(process_frame)
        insert_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=12, padx=(15, 0))

        ttk.Label(insert_frame, text="位置:").pack(side=tk.LEFT)
        self.current_ms_var = tk.StringVar()
        current_entry = ttk.Entry(insert_frame, textvariable=self.current_ms_var, width=12)
        current_entry.pack(side=tk.LEFT, padx=(8, 15))
        ttk.Label(insert_frame, text="毫秒").pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(insert_frame, text="时长:").pack(side=tk.LEFT)
        self.insert_silence_var = tk.DoubleVar(value=1.0)
        insert_spin = ttk.Spinbox(insert_frame, from_=0.1, to=10.0, increment=0.1,
                                  textvariable=self.insert_silence_var, width=8)
        insert_spin.pack(side=tk.LEFT, padx=(8, 8))
        ttk.Label(insert_frame, text="秒").pack(side=tk.LEFT)

        # 预览和操作按钮 - 去掉弹窗
        button_frame = ttk.LabelFrame(main_frame, text="操作控制", padding="15")
        button_frame.pack(fill=tk.X, pady=(0, 10))

        # 第一行按钮
        button_row1 = ttk.Frame(button_frame)
        button_row1.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(button_row1, text="播放原音频", command=self.play_original,
                   width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_row1, text="播放选区", command=self.play_selection,
                   width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_row1, text="预览效果", command=self.preview_audio,
                   width=15).pack(side=tk.LEFT, padx=(0, 10))

        # 第二行按钮
        button_row2 = ttk.Frame(button_frame)
        button_row2.pack(fill=tk.X, pady=(0, 0))

        ttk.Button(button_row2, text="应用处理", command=self.apply_processing,
                   width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_row2, text="重置所有", command=self.reset_values,
                   width=15).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_row2, text="取消", command=self.dialog.destroy,
                   width=15).pack(side=tk.LEFT)

        # 配置列权重，使内容能够扩展
        for frame in [info_frame, crop_frame, process_frame, button_frame]:
            frame.columnconfigure(1, weight=1)

        # 绑定事件
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
        """播放原音频 - 去掉弹窗"""
        if not self.line or not self.line.audio_path:
            messagebox.showwarning("警告", "音频文件不存在")
            return

        from app.services.audio_player_service import audio_player
        audio_player.play_audio(self.line.audio_path)
        # 去掉 messagebox.showinfo 弹窗

    def play_selection(self):
        """播放选定的时间区间 - 去掉弹窗"""
        if not self.validate_time_inputs():
            return

        try:
            start_ms = int(self.start_ms_var.get()) if self.start_ms_var.get() else 0
            end_ms = int(self.end_ms_var.get()) if self.end_ms_var.get() else self.audio_duration

            print(f"播放选区: {start_ms}-{end_ms}ms")

            # 使用ffmpeg裁剪并播放选定区间
            import tempfile
            import subprocess

            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"selection_{self.line_id}.wav")

            # 使用系统环境变量中的ffmpeg
            ffmpeg_path = "ffmpeg"

            ffmpeg_cmd = [
                ffmpeg_path, '-y', '-i', self.line.audio_path,
                '-ss', str(start_ms / 1000.0),
                '-to', str(end_ms / 1000.0),
                '-ac', '2', '-ar', '44100', '-acodec', 'pcm_s16le',
                temp_path
            ]

            print(f"选区FFmpeg命令: {' '.join(ffmpeg_cmd)}")

            # 执行ffmpeg命令
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

            if result.returncode == 0 and os.path.exists(temp_path):
                print(f"选区文件生成成功，大小: {os.path.getsize(temp_path)} 字节")
                from app.services.audio_player_service import audio_player
                if audio_player.play_audio(temp_path):
                    print("选区播放开始")
                else:
                    print("选区播放失败")
            else:
                print(f"选区文件生成失败，返回码: {result.returncode}")
                print(f"FFmpeg错误: {result.stderr}")
                messagebox.showerror("错误", "选区播放失败")

        except Exception as e:
            print(f"播放选区失败: {str(e)}")
            messagebox.showerror("错误", f"播放选区失败: {str(e)}")

    def preview_audio(self):
        """预览音频效果 - 修复权限问题"""
        if not self.validate_inputs():
            return

        try:
            # 构建处理参数
            dto = self.create_audio_dto()

            # 使用唯一文件名避免冲突
            import time
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"preview_{self.line_id}_{int(time.time() * 1000)}.wav")

            print(f"预览文件路径: {temp_path}")

            # 确保临时目录存在
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)

            # 先清理可能存在的旧文件
            self._cleanup_old_preview_files()

            # 处理音频
            success = self._process_audio_with_ffmpeg(self.line.audio_path, dto, temp_path)

            if success and os.path.exists(temp_path):
                print(f"预览文件生成成功，文件大小: {os.path.getsize(temp_path)} 字节")

                # 使用音频播放器播放预览
                from app.services.audio_player_service import audio_player

                # 先停止当前播放
                audio_player.stop_audio()

                # 短暂延迟确保文件释放
                import time
                time.sleep(0.1)

                if audio_player.play_audio(temp_path):
                    print("预览播放开始")

                    # 启动后台清理任务
                    self.dialog.after(5000, lambda: self._cleanup_temp_file(temp_path))
                else:
                    print("预览播放失败")
                    # 播放失败也清理文件
                    self._cleanup_temp_file(temp_path)
            else:
                print(f"预览文件生成失败，文件存在: {os.path.exists(temp_path)}")
                messagebox.showerror("错误", "预览生成失败")

        except Exception as e:
            print(f"预览失败详细错误: {str(e)}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("错误", f"预览失败: {str(e)}")

    def _cleanup_old_preview_files(self):
        """清理旧的预览文件"""
        try:
            import tempfile
            import time
            import glob

            temp_dir = tempfile.gettempdir()
            pattern = os.path.join(temp_dir, f"preview_{self.line_id}_*.wav")

            # 查找所有匹配的预览文件
            preview_files = glob.glob(pattern)

            for file_path in preview_files:
                try:
                    # 只删除超过1分钟的旧文件
                    file_age = time.time() - os.path.getctime(file_path)
                    if file_age > 60:  # 60秒
                        os.remove(file_path)
                        print(f"清理旧预览文件: {file_path}")
                except Exception as e:
                    print(f"清理文件失败 {file_path}: {e}")
                    # 忽略权限错误，继续处理其他文件

        except Exception as e:
            print(f"清理旧文件失败: {e}")

    def _cleanup_temp_file(self, file_path):
        """清理临时文件"""
        try:
            if os.path.exists(file_path):
                # 尝试多次删除，因为文件可能还在被占用
                for i in range(3):
                    try:
                        os.remove(file_path)
                        print(f"成功清理临时文件: {file_path}")
                        break
                    except PermissionError:
                        if i < 2:  # 前两次重试
                            import time
                            time.sleep(0.5)
                        else:
                            print(f"无法删除文件，可能仍在占用: {file_path}")
                    except Exception as e:
                        print(f"清理文件失败 {file_path}: {e}")
                        break
        except Exception as e:
            print(f"清理临时文件异常: {e}")

    def _process_audio_with_ffmpeg(self, input_path, dto, output_path):
        """使用ffmpeg直接处理音频 - 修复权限问题"""
        try:
            import subprocess

            # 使用系统环境变量中的ffmpeg
            ffmpeg_path = "ffmpeg"

            # 检查ffmpeg是否可用
            try:
                result = subprocess.run([ffmpeg_path, '-version'], capture_output=True, text=True)
                if result.returncode != 0:
                    # 如果直接调用失败，尝试在Windows上使用where命令查找
                    if os.name == 'nt':
                        where_result = subprocess.run(['where', 'ffmpeg'], capture_output=True, text=True)
                        if where_result.returncode == 0:
                            ffmpeg_path = where_result.stdout.strip().split('\n')[0]
                            print(f"通过where找到FFmpeg: {ffmpeg_path}")
                        else:
                            messagebox.showerror("错误", "在系统环境变量中找不到FFmpeg")
                            return False
                    else:
                        # Linux/Mac
                        which_result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
                        if which_result.returncode == 0:
                            ffmpeg_path = which_result.stdout.strip()
                            print(f"通过which找到FFmpeg: {ffmpeg_path}")
                        else:
                            messagebox.showerror("错误", "在系统环境变量中找不到FFmpeg")
                            return False
            except Exception as e:
                print(f"FFmpeg检查失败: {e}")
                messagebox.showerror("错误", f"FFmpeg检查失败: {e}")
                return False

            # 检查输入文件是否存在
            if not os.path.exists(input_path):
                messagebox.showerror("错误", f"输入文件不存在: {input_path}")
                return False

            print(f"处理参数: 速度={dto.speed}, 音量={dto.volume}, 裁剪={dto.start_ms}-{dto.end_ms}")

            # 如果输出文件已存在，先删除
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                    print(f"删除已存在的输出文件: {output_path}")
                except PermissionError:
                    print(f"无法删除已存在的文件，尝试使用新文件名: {output_path}")
                    # 如果无法删除，生成新文件名
                    import time
                    output_path = output_path.replace('.wav', f'_{int(time.time() * 1000)}.wav')
                    print(f"使用新文件名: {output_path}")

            # 构建基础命令
            cmd = [ffmpeg_path, '-y', '-i', input_path]

            # 简化处理：使用简单滤镜链
            filter_parts = []

            # 处理裁剪
            if dto.start_ms is not None and dto.end_ms is not None and dto.end_ms > dto.start_ms:
                if dto.crop_mode == "keep":
                    # 保留模式：只保留选定区间
                    cmd.extend(['-ss', str(dto.start_ms / 1000.0), '-to', str(dto.end_ms / 1000.0)])
                else:
                    # 删除模式：使用atrim和concat
                    filter_complex = f"atrim=0:{dto.start_ms / 1000.0},asetpts=PTS-STARTPTS[a1];atrim={dto.end_ms / 1000.0},asetpts=PTS-STARTPTS[a2];[a1][a2]concat=n=2:v=0:a=1"
                    filter_parts.append(filter_complex)

            # 变速
            if dto.speed != 1.0:
                filter_parts.append(f"atempo={dto.speed}")

            # 音量
            if dto.volume != 1.0:
                filter_parts.append(f"volume={dto.volume}")

            # 静音处理（简化版）
            if dto.silence_sec != 0 and dto.current_ms is None:
                if dto.silence_sec > 0:
                    filter_parts.append(f"apad=pad_dur={dto.silence_sec}")

            # 应用滤镜
            if filter_parts:
                filter_chain = ",".join(filter_parts)
                cmd.extend(['-af', filter_chain])

            # 添加输出参数
            cmd.extend([
                '-ac', '2', '-ar', '44100', '-acodec', 'pcm_s16le',
                output_path
            ])

            print(f"FFmpeg命令: {' '.join(cmd)}")

            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

            if result.returncode == 0:
                print("FFmpeg处理成功")
                if os.path.exists(output_path):
                    print(f"输出文件大小: {os.path.getsize(output_path)} 字节")
                    return True
                else:
                    print("FFmpeg处理成功但输出文件不存在")
                    return False
            else:
                print(f"FFmpeg处理失败，返回码: {result.returncode}")
                print(f"FFmpeg错误输出: {result.stderr}")
                return False

        except Exception as e:
            print(f"FFmpeg处理异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def apply_processing(self):
        """应用音频处理"""
        if not self.validate_inputs():
            return

        try:
            # 构建处理参数
            dto = self.create_audio_dto()

            # 直接使用FFmpeg处理原文件，不依赖line_service的方法
            success = self._apply_audio_processing(dto)

            if success:
                messagebox.showinfo("成功", "音频处理完成")
                self.dialog.destroy()
            else:
                messagebox.showerror("错误", "音频处理失败")

        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")

    def _apply_audio_processing(self, dto):
        """直接应用音频处理到原文件"""
        try:
            import tempfile
            import shutil

            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"processed_{self.line_id}.wav")

            print(f"应用处理到文件: {self.line.audio_path}")
            print(f"临时文件: {temp_path}")

            # 使用FFmpeg处理音频到临时文件
            success = self._process_audio_with_ffmpeg(self.line.audio_path, dto, temp_path)

            if success and os.path.exists(temp_path):
                # 备份原文件
                backup_path = self.line.audio_path + '.backup'
                try:
                    shutil.copy2(self.line.audio_path, backup_path)
                    print(f"原文件已备份到: {backup_path}")
                except Exception as e:
                    print(f"备份失败: {e}")

                # 用处理后的文件替换原文件
                shutil.copy2(temp_path, self.line.audio_path)
                print(f"文件替换完成")

                # 清理临时文件
                try:
                    os.remove(temp_path)
                except:
                    pass

                # 更新数据库状态（如果需要）
                try:
                    self.line_controller.update_line(self.line_id, {"status": "done"})
                except:
                    print("数据库状态更新失败，但文件处理成功")

                return True
            else:
                print("FFmpeg处理失败")
                return False

        except Exception as e:
            print(f"应用处理失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def validate_time_inputs(self):
        """验证时间输入"""
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

    def validate_inputs(self):
        """验证所有输入参数"""
        if not self.line or not self.line.audio_path:
            messagebox.showwarning("警告", "音频文件不存在")
            return False

        return self.validate_time_inputs()

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