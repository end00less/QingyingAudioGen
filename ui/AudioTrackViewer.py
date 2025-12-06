import flet as ft
import flet.canvas as cv
import threading
import time
import tempfile
import os
import subprocess
import numpy as np
import wave
from typing import Optional


class AudioTrackViewer(ft.Container):
    """简化的音频轨道查看器"""

    def __init__(self, line, width=400, height=120, on_selection_change=None):
        super().__init__()
        self.line = line
        self.width = width
        self.height = height
        self.on_selection_change = on_selection_change

        # 音频数据
        self.audio_path = getattr(line, 'audio_path', None)
        self.duration = 0
        self.waveform_data = None

        # 选择状态
        self.is_selecting = False
        self.selection_start = None
        self.selection_end = None

        # 播放状态
        self.is_playing = False
        self.playback_progress = 0

        # UI组件
        self.canvas = None
        self.progress_indicator = None
        self.selection_rect = None
        self.timeline_text = None
        self.selection_text = None

        self.content = self._create_layout()

        # 延迟加载音频数据
        if self.audio_path and os.path.exists(self.audio_path):
            threading.Thread(target=self._load_audio_data, daemon=True).start()

    def _create_layout(self):
        """创建布局"""
        # 创建Canvas
        self.canvas = cv.Canvas(
            width=self.width - 20,
            height=self.height - 40,
            expand=False
        )

        # 播放进度指示器
        self.progress_indicator = ft.Container(
            width=2,
            height=self.height - 40,
            bgcolor=ft.Colors.RED,
            left=0,
            top=0,
            opacity=0,
            animate_position=200
        )

        # 选择区域
        self.selection_rect = ft.Container(
            width=0,
            height=self.height - 40,
            bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.BLUE),
            left=0,
            top=0,
            opacity=0
        )

        # 时间显示
        self.timeline_text = ft.Text("00:00 / 00:00", size=10, color=ft.Colors.GREY_600)
        self.selection_text = ft.Text("未选择区域", size=10, color=ft.Colors.BLUE_600)

        # 叠加层
        stack = ft.Stack([
            self.canvas,
            self.selection_rect,
            self.progress_indicator
        ], width=self.width - 20, height=self.height - 40)

        return ft.Column([
            # 波形显示区
            ft.Container(
                content=stack,
                width=self.width,
                height=self.height - 40,
                bgcolor=ft.Colors.WHITE,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=5,
                on_click=self._on_canvas_click,
                on_hover=self._on_canvas_hover
            ),

            # 时间轴和选择信息
            ft.Container(
                content=ft.Row([
                    self.timeline_text,
                    ft.Container(width=10),
                    self.selection_text
                ], spacing=5),
                width=self.width,
                height=20,
                bgcolor=ft.Colors.GREY_50,
                padding=ft.padding.symmetric(5, 2)
            )
        ], spacing=0)

    def _load_audio_data(self):
        """加载音频数据"""
        try:
            if not self.audio_path or not os.path.exists(self.audio_path):
                return

            # 读取音频文件
            with wave.open(self.audio_path, 'rb') as wav_file:
                self.duration = wav_file.getnframes() / wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                audio_data = np.frombuffer(frames, dtype=np.int16)

                # 如果是立体声，转换为单声道
                if wav_file.getnchannels() == 2:
                    audio_data = audio_data.reshape(-1, 2).mean(axis=1).astype(np.int16)

                # 降采样
                max_points = min(self.canvas.width, 200)
                if len(audio_data) > max_points:
                    step = len(audio_data) // max_points
                    audio_data = audio_data[::step]

                self.waveform_data = audio_data.astype(np.float32) / 32768.0

                # 在主线程中更新UI
                self.page.call_threadsafe(self._draw_waveform)

        except Exception as e:
            print(f"加载音频数据失败: {e}")

    def _draw_waveform(self):
        """绘制波形"""
        try:
            if self.waveform_data is None:
                self._draw_empty_state()
                return

            canvas_width = self.canvas.width
            canvas_height = self.canvas.height
            center_y = canvas_height / 2

            # 清空画布
            shapes = [
                cv.Rect(0, 0, canvas_width, canvas_height,
                        paint=ft.Paint(color=ft.Colors.WHITE))
            ]

            # 绘制波形
            n_points = len(self.waveform_data)
            for i in range(n_points):
                x = (i / n_points) * canvas_width
                amplitude = self.waveform_data[i]
                y = center_y - (amplitude * center_y * 0.8)

                if i > 0:
                    prev_x = ((i - 1) / n_points) * canvas_width
                    prev_amplitude = self.waveform_data[i - 1]
                    prev_y = center_y - (prev_amplitude * center_y * 0.8)

                    shapes.append(cv.Line(
                        prev_x, prev_y, x, y,
                        paint=ft.Paint(color=ft.Colors.BLUE_600, stroke_width=1)
                    ))

            self.canvas.shapes = shapes
            self.canvas.update()

            # 更新时间显示
            self._update_timeline_display()

        except Exception as e:
            print(f"绘制波形失败: {e}")
            self._draw_empty_state()

    def _draw_empty_state(self):
        """绘制空状态"""
        try:
            self.canvas.shapes = [
                cv.Rect(0, 0, self.canvas.width, self.canvas.height,
                        paint=ft.Paint(color=ft.Colors.WHITE)),
                cv.Text(
                    "无音频文件",
                    self.canvas.width // 2 - 30,
                    self.canvas.height // 2,
                    style=ft.TextStyle(color=ft.Colors.GREY_400, size=12)
                )
            ]
            self.canvas.update()
        except Exception as e:
            print(f"绘制空状态失败: {e}")

    def _update_timeline_display(self):
        """更新时间显示"""
        try:
            if self.duration > 0:
                minutes = int(self.duration // 60)
                seconds = int(self.duration % 60)
                self.timeline_text.value = f"00:00 / {minutes:02d}:{seconds:02d}"
            else:
                self.timeline_text.value = "00:00 / 00:00"
            self.timeline_text.update()
        except Exception as e:
            print(f"更新时间显示失败: {e}")

    def _on_canvas_click(self, e):
        """Canvas点击事件"""
        if not self.waveform_data:
            return

        x = e.local_x
        canvas_width = self.canvas.width

        if x < 0 or x > canvas_width:
            return

        # 检查是否双击
        current_time = time.time()
        if hasattr(self, '_last_click_time'):
            if current_time - self._last_click_time < 0.3:
                self._start_selection(x)
                self._last_click_time = 0
                return

        self._last_click_time = current_time

        # 单击播放
        start_time = (x / canvas_width) * self.duration
        self._play_from_time(start_time)

    def _on_canvas_hover(self, e):
        """Canvas悬停事件"""
        if not self.waveform_data or self.duration <= 0:
            return

        x = e.local_x
        canvas_width = self.canvas.width

        if 0 <= x <= canvas_width:
            current_time = (x / canvas_width) * self.duration
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            total_minutes = int(self.duration // 60)
            total_seconds = int(self.duration % 60)

            self.timeline_text.value = f"{minutes:02d}:{seconds:02d} / {total_minutes:02d}:{total_seconds:02d}"
            self.timeline_text.update()

    def _start_selection(self, x):
        """开始选择区域"""
        self.is_selecting = True
        self.selection_start = x
        self.selection_end = x

        # 显示选择矩形
        self.selection_rect.width = 0
        self.selection_rect.left = x
        self.selection_rect.opacity = 1
        self.selection_rect.update()

        # 绑定鼠标移动事件（简化处理）
        self.show_snack_bar("开始选择区域，拖动鼠标调整范围")

    def _play_from_time(self, start_time):
        """从指定时间播放"""
        if not self.audio_path or not os.path.exists(self.audio_path):
            self.show_snack_bar("音频文件不存在")
            return

        try:
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            timestamp = int(time.time() * 1000)
            temp_path = os.path.join(temp_dir, f"preview_{timestamp}.wav")

            # 使用FFmpeg裁剪音频
            duration = min(5.0, self.duration - start_time)  # 最多播放5秒
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", self.audio_path,
                "-ss", str(start_time),
                "-t", str(duration),
                "-acodec", "pcm_s16le",
                temp_path
            ]

            def play_audio():
                try:
                    result = subprocess.run(
                        ffmpeg_cmd,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )

                    if result.returncode == 0 and os.path.exists(temp_path):
                        # 模拟播放
                        self._start_playback_animation(duration)
                        time.sleep(duration)
                        self._stop_playback_animation()

                        # 清理临时文件
                        try:
                            os.remove(temp_path)
                        except:
                            pass
                    else:
                        self.show_snack_bar("音频处理失败")

                except Exception as e:
                    print(f"播放音频失败: {e}")
                    self.show_snack_bar("播放失败")

            threading.Thread(target=play_audio, daemon=True).start()

        except Exception as e:
            print(f"播放音频失败: {e}")
            self.show_snack_bar("播放失败")

    def _start_playback_animation(self, duration):
        """开始播放动画"""
        self.is_playing = True
        self.progress_indicator.opacity = 1
        self.progress_indicator.update()

        start_time = time.time()

        def update_progress():
            if not self.is_playing:
                return

            elapsed = time.time() - start_time
            progress = min(elapsed / duration, 1.0)

            # 更新进度指示器位置
            canvas_width = self.canvas.width
            self.progress_indicator.left = progress * canvas_width
            self.progress_indicator.update()

            if progress < 1.0:
                threading.Timer(0.05, update_progress).start()
            else:
                self._stop_playback_animation()

        update_progress()

    def _stop_playback_animation(self):
        """停止播放动画"""
        self.is_playing = False
        self.progress_indicator.opacity = 0
        self.progress_indicator.left = 0
        self.progress_indicator.update()

    def clear_selection(self):
        """清除选择"""
        self.selection_start = None
        self.selection_end = None
        self.selection_rect.opacity = 0
        self.selection_rect.update()
        self.selection_text.value = "未选择区域"
        self.selection_text.update()

    def show_snack_bar(self, message):
        """显示提示信息"""
        if hasattr(self, 'page') and self.page:
            snack = ft.SnackBar(content=ft.Text(message), duration=2000)
            self.page.overlay.append(snack)
            self.page.update()
            snack.open = True
            self.page.update()
