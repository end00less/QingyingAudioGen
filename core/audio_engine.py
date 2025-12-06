# app/core/audio_engine.py
import os
import subprocess
import tempfile
import soundfile as sf
import numpy as np
from typing import Optional
import sys


class AudioProcessor:
    def __init__(self, audio_path: str, keep_format=True, default_sr=44100, default_ch=2):
        self.audio_path = audio_path
        self.keep_format = keep_format
        self.default_sr = default_sr
        self.default_ch = default_ch

        # 获取音频文件信息
        try:
            info = sf.info(audio_path)
            self.sr = info.samplerate if keep_format else default_sr
            self.ch = info.channels if keep_format else default_ch
            self.duration = info.duration
        except Exception as e:
            print(f"音频文件信息获取失败: {e}")
            self.sr = default_sr
            self.ch = default_ch
            self.duration = 0

        self.ffmpeg_path = self._get_ffmpeg_path()
        self.temp_path = self._create_tmp_file()

    def _get_ffmpeg_path(self) -> str:
        """获取FFmpeg路径 - 桌面版适配"""
        # 优先检查系统PATH中的ffmpeg
        if sys.platform == "win32":
            # Windows系统
            possible_paths = [
                "ffmpeg.exe",
                os.path.join(os.getcwd(), "ffmpeg", "ffmpeg.exe"),
                os.path.join(os.path.dirname(__file__), "ffmpeg", "ffmpeg.exe"),
            ]
        else:
            # Linux/Mac系统
            possible_paths = [
                "ffmpeg",
                "/usr/bin/ffmpeg",
                "/usr/local/bin/ffmpeg",
                os.path.join(os.getcwd(), "ffmpeg", "ffmpeg"),
            ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 如果找不到，尝试在PATH中查找
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return "ffmpeg"
        except:
            raise FileNotFoundError("未找到FFmpeg，请安装FFmpeg并添加到系统PATH，或放置在程序目录下的ffmpeg文件夹中")

    def _create_tmp_file(self) -> str:
        """创建临时文件"""
        os.makedirs(os.path.dirname(self.audio_path) or ".", exist_ok=True)
        tmp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".wav",
            dir=os.path.dirname(self.audio_path) or "."
        )
        return tmp.name

    def _run_ffmpeg(self, cmd):
        """运行FFmpeg命令"""
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg执行失败: {e}")
            print(f"错误输出: {e.stderr}")
            raise
        except FileNotFoundError:
            print("FFmpeg未找到，请确保已正确安装")
            raise

    def _normalize(self, path):
        """防止音量削波 - 音频归一化"""
        try:
            data, sr = sf.read(path, dtype="float32", always_2d=True)
            peak = float(np.max(np.abs(data)))
            if peak > 1.0:
                data = data / peak
                sf.write(path, data, sr, format="WAV", subtype="PCM_16")
        except Exception as e:
            print(f"音频归一化失败: {e}")

    # ---------------------- 核心音频处理功能 ----------------------

    def cut(self, start_ms: int, end_ms: int):
        """删除音频区间 [start_ms, end_ms]"""
        if start_ms >= end_ms:
            raise ValueError("开始时间必须小于结束时间")

        start_sec = start_ms / 1000
        end_sec = end_ms / 1000

        cmd = [
            self.ffmpeg_path, "-y", "-i", self.audio_path,
            "-filter_complex",
            f"[0:a]atrim=0:{start_sec},asetpts=PTS-STARTPTS[first];"
            f"[0:a]atrim={end_sec},asetpts=PTS-STARTPTS[second];"
            f"[first][second]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            "-ar", str(self.sr),
            "-ac", str(self.ch),
            "-c:a", "pcm_s16le",
            self.temp_path
        ]

        self._run_ffmpeg(cmd)
        os.replace(self.temp_path, self.audio_path)

        # 更新音频信息
        self._update_audio_info()

    def insert_silence(self, insert_ms: int, duration_sec: float):
        """在指定时间点插入静音"""
        insert_sec = insert_ms / 1000

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", self.audio_path,
            "-f", "lavfi", "-t", str(duration_sec),
            "-i", f"anullsrc=channel_layout={'stereo' if self.ch == 2 else 'mono'}:sample_rate={self.sr}",
            "-filter_complex",
            f"[0:a]atrim=0:{insert_sec},asetpts=PTS-STARTPTS[first];"
            f"[0:a]atrim={insert_sec},asetpts=PTS-STARTPTS[second];"
            f"[first][1:a][second]concat=n=3:v=0:a=1[out]",
            "-map", "[out]",
            "-ar", str(self.sr),
            "-ac", str(self.ch),
            "-c:a", "pcm_s16le",
            self.temp_path
        ]

        self._run_ffmpeg(cmd)
        os.replace(self.temp_path, self.audio_path)
        self._update_audio_info()

    def append_silence(self, duration_sec: float):
        """
        在音频末尾添加或裁剪静音段：
        - duration_sec > 0: 在末尾添加指定秒数静音
        - duration_sec < 0: 从末尾裁剪指定秒数的内容
        """
        if duration_sec == 0:
            return  # 无需处理

        # ---------- 情况1：添加静音 ----------
        if duration_sec > 0:
            cmd = [
                self.ffmpeg_path, "-y",
                "-i", self.audio_path,
                "-f", "lavfi", "-t", str(duration_sec),
                "-i", f"anullsrc=channel_layout={'stereo' if self.ch == 2 else 'mono'}:sample_rate={self.sr}",
                "-filter_complex",
                "[0:a][1:a]concat=n=2:v=0:a=1[out]",
                "-map", "[out]",
                "-ar", str(self.sr),
                "-ac", str(self.ch),
                "-c:a", "pcm_s16le",
                self.temp_path
            ]

        # ---------- 情况2：裁剪末尾 ----------
        else:
            cut_dur = self.duration + duration_sec  # 因为 duration_sec 为负
            if cut_dur < 0:
                cut_dur = 0  # 防止全裁掉出错
            cmd = [
                self.ffmpeg_path, "-y",
                "-i", self.audio_path,
                "-filter_complex",
                f"[0:a]atrim=0:{cut_dur},asetpts=PTS-STARTPTS[out]",
                "-map", "[out]",
                "-ar", str(self.sr),
                "-ac", str(self.ch),
                "-c:a", "pcm_s16le",
                self.temp_path
            ]

        # 执行 ffmpeg 命令
        self._run_ffmpeg(cmd)
        os.replace(self.temp_path, self.audio_path)
        self._update_audio_info()

    def change_speed(self, speed: float):
        """变速处理 (0.5~2.0倍)"""
        speed = float(np.clip(speed, 0.5, 2.0))
        cmd = [
            self.ffmpeg_path, "-y", "-i", self.audio_path,
            "-af", f"atempo={speed}",
            "-ar", str(self.sr),
            "-ac", str(self.ch),
            "-c:a", "pcm_s16le",
            self.temp_path
        ]
        self._run_ffmpeg(cmd)
        os.replace(self.temp_path, self.audio_path)
        self._update_audio_info()

    def change_volume(self, volume: float):
        """音量调整"""
        volume = max(0.0, float(volume))
        cmd = [
            self.ffmpeg_path, "-y", "-i", self.audio_path,
            "-af", f"volume={volume}",
            "-ar", str(self.sr),
            "-ac", str(self.ch),
            "-c:a", "pcm_s16le",
            self.temp_path
        ]
        self._run_ffmpeg(cmd)
        os.replace(self.temp_path, self.audio_path)

    def merge_audios(self, audio_paths: list, output_path: str):
        """合并多个音频文件"""
        if not audio_paths:
            raise ValueError("音频文件列表不能为空")

        # 创建文件列表
        list_file = self.temp_path + "_list.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for audio_path in audio_paths:
                f.write(f"file '{os.path.abspath(audio_path)}'\n")

        cmd = [
            self.ffmpeg_path, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            output_path
        ]

        try:
            self._run_ffmpeg(cmd)
        finally:
            # 清理临时文件
            if os.path.exists(list_file):
                os.remove(list_file)

        return output_path

    def get_audio_info(self) -> dict:
        """获取音频文件信息"""
        try:
            info = sf.info(self.audio_path)
            return {
                'duration': info.duration,
                'sample_rate': info.samplerate,
                'channels': info.channels,
                'format': info.format
            }
        except Exception as e:
            print(f"获取音频信息失败: {e}")
            return {}

    def _update_audio_info(self):
        """更新音频信息"""
        try:
            info = sf.info(self.audio_path)
            self.duration = info.duration
            self.sr = info.samplerate
            self.ch = info.channels
        except Exception as e:
            print(f"更新音频信息失败: {e}")

    def export(self, out_path: str):
        """导出音频到目标路径（带软限幅）"""
        self._normalize(self.audio_path)
        os.replace(self.audio_path, out_path)
        return out_path

    def preview_audio(self, start_ms: int = 0, duration_ms: int = 5000) -> str:
        """生成预览音频片段"""
        start_sec = start_ms / 1000
        duration_sec = duration_ms / 1000

        preview_path = self.temp_path + "_preview.wav"

        cmd = [
            self.ffmpeg_path, "-y",
            "-i", self.audio_path,
            "-ss", str(start_sec),
            "-t", str(duration_sec),
            "-ar", str(self.sr),
            "-ac", str(self.ch),
            "-c:a", "pcm_s16le",
            preview_path
        ]

        self._run_ffmpeg(cmd)
        return preview_path

    def cleanup(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.temp_path):
                os.remove(self.temp_path)
        except:
            pass


# 音频工具函数
class AudioUtils:
    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化时间显示"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    @staticmethod
    def is_audio_file(file_path: str) -> bool:
        """检查是否为支持的音频文件"""
        supported_formats = ['.wav', '.mp3', '.flac', '.m4a', '.aac']
        ext = os.path.splitext(file_path)[1].lower()
        return ext in supported_formats

    @staticmethod
    def get_supported_formats() -> list:
        """获取支持的音频格式"""
        return ['WAV (*.wav)', 'MP3 (*.mp3)', 'FLAC (*.flac)', 'M4A (*.m4a)']


# 音频播放器类（简单的音频播放功能）
class AudioPlayer:
    def __init__(self):
        self.is_playing = False
        self.current_process = None

    def play_audio(self, audio_path: str):
        """播放音频文件"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        try:
            # 使用系统默认播放器
            if sys.platform == "win32":
                os.startfile(audio_path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["afplay", audio_path])
            else:  # Linux
                subprocess.run(["aplay", audio_path])

            self.is_playing = True
            return True
        except Exception as e:
            print(f"播放音频失败: {e}")
            return False

    def stop_audio(self):
        """停止播放"""
        # 注意：这种方法可能无法停止系统播放器
        self.is_playing = False
        if self.current_process:
            try:
                self.current_process.terminate()
            except:
                pass