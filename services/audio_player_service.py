# app/services/audio_player_service.py
import pygame
import os
import threading
from typing import Optional


class AudioPlayerService:
    def __init__(self):
        pygame.mixer.init()
        self.current_playing: Optional[str] = None
        self.is_playing = False

    def play_audio(self, file_path: str) -> bool:
        """播放音频文件"""
        if not os.path.exists(file_path):
            return False

        try:
            # 如果正在播放，先停止
            if self.is_playing:
                self.stop_audio()

            # 加载并播放音频
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()

            self.current_playing = file_path
            self.is_playing = True

            # 在后台线程中监控播放状态
            def monitor_playback():
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)
                self.is_playing = False
                self.current_playing = None

            threading.Thread(target=monitor_playback, daemon=True).start()
            return True

        except Exception as e:
            print(f"播放音频失败: {e}")
            return False

    def stop_audio(self):
        """停止播放"""
        try:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.current_playing = None
        except Exception as e:
            print(f"停止音频失败: {e}")

    def is_playing_audio(self, file_path: str = None) -> bool:
        """检查是否正在播放音频"""
        if file_path:
            return self.is_playing and self.current_playing == file_path
        return self.is_playing


# 全局音频播放器实例
audio_player = AudioPlayerService()