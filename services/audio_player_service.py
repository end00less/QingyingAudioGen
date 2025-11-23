# app/services/audio_player_service.py
import threading
import time
import os
import subprocess
import platform
from typing import Optional

# 尝试导入pygame，如果失败则使用备选方案
try:
    import pygame

    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    USING_PYGAME = True
    print("使用pygame播放音频")
except ImportError:
    print("警告: 未安装pygame，将使用备选方案")
    print("请运行: pip install pygame")
    USING_PYGAME = False
except Exception as e:
    print(f"pygame初始化失败: {e}，将使用备选方案")
    USING_PYGAME = False

# 备选方案：使用pydub + simpleaudio
try:
    from pydub import AudioSegment
    import simpleaudio as sa

    USING_PYDUB = True
    print("使用pydub + simpleaudio播放音频")
except ImportError:
    USING_PYDUB = False
    if not USING_PYGAME:
        print("警告: 未安装pydub和simpleaudio")
        print("请运行: pip install pydub simpleaudio")

# 最后备选：使用系统命令
USING_SYSTEM = True


class AudioPlayerService:
    def __init__(self):
        self.is_playing = False
        self.stop_playback = False
        self.current_audio = None
        self.play_thread = None
        self.duration = 0  # 音频时长（秒）
        self.position = 0  # 当前播放位置（秒）
        self._lock = threading.Lock()  # 添加线程锁

        # 播放方式优先级
        self.playback_method = self._detect_best_method()

    def _detect_best_method(self):
        """检测最佳播放方法"""
        if USING_PYGAME:
            return "pygame"
        elif USING_PYDUB:
            return "pydub"
        elif USING_SYSTEM:
            return "system"
        else:
            return "none"

    def play_audio(self, file_path: str) -> bool:
        """播放音频 - 使用多种方法"""
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False

        try:
            # 如果正在播放，先停止
            if self.is_playing:
                self.stop_audio()

            self.is_playing = True
            self.stop_playback = False
            self.position = 0

            # 获取音频时长
            self.duration = self._get_audio_duration(file_path)

            # 尝试不同的播放方法
            methods = ["pygame", "pydub", "system"]

            for method in methods:
                try:
                    if method == "pygame" and USING_PYGAME:
                        if self._play_with_pygame(file_path):
                            return True
                    elif method == "pydub" and USING_PYDUB:
                        if self._play_with_pydub(file_path):
                            return True
                    elif method == "system" and USING_SYSTEM:
                        if self._play_with_system(file_path):
                            return True
                except Exception as e:
                    print(f"{method}播放失败: {e}")
                    continue

            # 所有方法都失败
            print("所有播放方法都失败了")
            self.is_playing = False
            return False

        except Exception as e:
            print(f"播放音频失败: {e}")
            self.is_playing = False
            return False

    def _play_with_pygame(self, file_path: str) -> bool:
        """使用pygame播放音频"""
        try:
            # 尝试直接加载
            try:
                pygame.mixer.music.load(file_path)
            except pygame.error as e:
                if "Unknown WAVE format" in str(e):
                    # 尝试转换格式
                    print("WAV格式不兼容，尝试转换...")
                    converted_path = self._convert_wav_format(file_path)
                    if converted_path:
                        pygame.mixer.music.load(converted_path)
                    else:
                        raise e
                else:
                    raise e

            pygame.mixer.music.play()

            # 创建监控线程
            def monitor_playback():
                while pygame.mixer.music.get_busy() and not self.stop_playback:
                    time.sleep(0.1)
                    self.position += 0.1

                if not self.stop_playback:
                    pygame.mixer.music.stop()

                with self._lock:
                    self.is_playing = False
                    self.position = 0

            self.play_thread = threading.Thread(target=monitor_playback, daemon=True)
            self.play_thread.start()
            return True

        except Exception as e:
            print(f"pygame播放失败: {e}")
            return False

    def _play_with_pydub(self, file_path: str) -> bool:
        """使用pydub + simpleaudio播放音频"""
        try:
            # 使用pydub加载音频文件
            audio = AudioSegment.from_file(file_path)

            # 转换为simpleaudio可播放的格式
            if audio.channels == 1:
                audio = audio.set_channels(2)  # 转换为立体声

            # 转换为16位PCM
            audio = audio.set_sample_width(2)

            # 播放音频 - 确保成功
            try:
                playback_obj = sa.play_buffer(
                    audio.raw_data,
                    num_channels=audio.channels,
                    bytes_per_sample=audio.sample_width,
                    sample_rate=audio.frame_rate
                )
            except Exception as e:
                print(f"simpleaudio播放失败: {e}")
                return False

            # 检查播放对象是否有效
            if playback_obj is None:
                print("simpleaudio返回了None对象")
                return False

            # 设置当前音频对象
            with self._lock:
                self.current_audio = playback_obj

            print("音频开始播放")

            # 创建监控线程
            def monitor_playback():
                try:
                    while True:
                        with self._lock:
                            # 检查是否应该停止
                            if self.stop_playback:
                                break

                            # 检查当前音频对象
                            if self.current_audio is None:
                                break

                            # 检查是否还在播放
                            if not self.current_audio.is_playing():
                                break

                        time.sleep(0.1)
                        self.position += 0.1

                    # 播放结束或被停止
                    with self._lock:
                        if self.current_audio and not self.stop_playback:
                            try:
                                self.current_audio.stop()
                            except:
                                pass

                        self.is_playing = False
                        self.position = 0
                        self.current_audio = None

                    print("音频播放完成")

                except Exception as e:
                    print(f"监控线程出错: {e}")
                    with self._lock:
                        self.is_playing = False
                        self.position = 0
                        self.current_audio = None

            self.play_thread = threading.Thread(target=monitor_playback, daemon=True)
            self.play_thread.start()
            return True

        except Exception as e:
            print(f"pydub播放失败: {e}")
            return False

    def _play_with_system(self, file_path: str) -> bool:
        """使用系统命令播放（改进版）"""
        try:
            system = platform.system()

            if system == "Windows":
                # 使用Windows Media Player COM组件（无窗口）
                try:
                    import pythoncom
                    from win32com.client import Dispatch

                    def play_thread():
                        try:
                            pythoncom.CoInitialize()
                            wmp = Dispatch("WMPlayer.OCX")
                            wmp.URL = file_path
                            wmp.controls.play()

                            # 等待播放完成
                            while wmp.playState != 1 and not self.stop_playback:  # 1 = stopped
                                time.sleep(0.1)
                                self.position += 0.1

                            if not self.stop_playback:
                                wmp.controls.stop()

                            with self._lock:
                                self.is_playing = False
                                self.position = 0
                        except Exception as e:
                            print(f"Windows Media Player播放失败: {e}")
                        finally:
                            pythoncom.CoUninitialize()

                    self.play_thread = threading.Thread(target=play_thread, daemon=True)
                    self.play_thread.start()
                    return True

                except ImportError:
                    # 备选：使用PowerShell
                    ps_command = f'''
                    Add-Type -AssemblyName presentationCore
                    $mediaPlayer = New-Object system.windows.media.mediaplayer
                    $mediaPlayer.open("{file_path}")
                    $mediaPlayer.Play()
                    Start-Sleep -Seconds 10
                    '''
                    subprocess.Popen([
                        'powershell', '-WindowStyle', 'Hidden', '-Command', ps_command
                    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                    # 模拟播放状态
                    def simulate_playback():
                        time.sleep(10)
                        if not self.stop_playback:
                            with self._lock:
                                self.is_playing = False
                                self.position = 0

                    self.play_thread = threading.Thread(target=simulate_playback, daemon=True)
                    self.play_thread.start()
                    return True

            elif system == "Darwin":  # macOS
                subprocess.Popen(['afplay', file_path],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                # macOS的afplay会阻塞直到播放完成
                with self._lock:
                    self.is_playing = False
                return True

            else:  # Linux
                subprocess.Popen(['aplay', file_path],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                # Linux的aplay会阻塞直到播放完成
                with self._lock:
                    self.is_playing = False
                return True

        except Exception as e:
            print(f"系统命令播放失败: {e}")
            return False

    def _convert_wav_format(self, file_path: str) -> Optional[str]:
        """转换WAV文件格式"""
        try:
            if USING_PYDUB:
                # 使用pydub转换格式
                audio = AudioSegment.from_wav(file_path)

                # 转换为标准PCM格式
                audio = audio.set_channels(2)  # 立体声
                audio = audio.set_sample_width(2)  # 16位
                audio = audio.set_frame_rate(44100)  # 44.1kHz

                # 保存临时文件
                temp_path = file_path.replace('.wav', '_converted.wav')
                audio.export(temp_path, format='wav')

                print(f"WAV文件已转换: {temp_path}")
                return temp_path
            else:
                print("pydub不可用，无法转换WAV格式")
                return None

        except Exception as e:
            print(f"WAV格式转换失败: {e}")
            return None

    def stop_audio(self):
        """停止播放"""
        with self._lock:
            self.stop_playback = True

            if USING_PYGAME and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            elif USING_PYDUB and self.current_audio:
                try:
                    self.current_audio.stop()
                except:
                    pass
                self.current_audio = None

            self.is_playing = False
            self.position = 0

    def get_position(self) -> float:
        """获取当前播放位置（秒）"""
        return self.position

    def get_duration(self) -> float:
        """获取音频总时长（秒）"""
        return self.duration

    def _get_audio_duration(self, file_path: str) -> float:
        """获取音频时长"""
        try:
            # 尝试使用mutagen
            import mutagen
            audio = mutagen.File(file_path)
            if audio is not None:
                return audio.info.length
        except:
            pass

        # 尝试使用pydub
        if USING_PYDUB:
            try:
                audio = AudioSegment.from_file(file_path)
                return len(audio) / 1000.0  # 转换为秒
            except:
                pass

        # 备选方案：使用wave库（仅适用于WAV文件）
        try:
            import wave
            with wave.open(file_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except:
            pass

        # 默认返回0
        return 0

    def set_volume(self, volume: float):
        """设置音量 (0.0 - 1.0)"""
        if USING_PYGAME:
            pygame.mixer.music.set_volume(volume)


# 全局音频播放器实例
audio_player = AudioPlayerService()
