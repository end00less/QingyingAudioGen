import os
import json
from typing import Dict, Any


class Settings:
    def __init__(self):
        self.settings_dir = os.path.join(os.path.expanduser("~"), "SonicVale")
        self.settings_file = os.path.join(self.settings_dir, "settings.json")
        self.default_settings = {
            "llm_providers": {
                "openai": {
                    "api_base_url": "https://api.openai.com/v1",
                    "api_key": "",
                    "models": ["gpt-3.5-turbo", "gpt-4"]
                }
            },
            "tts_providers": {
                "default": {
                    "api_base_url": "http://127.0.0.1:8000",
                    "api_key": ""
                }
            },
            "audio_settings": {
                "sample_rate": 44100,
                "channels": 2,
                "default_volume": 1.0
            }
        }
        self.settings = self.load_settings()

    def load_settings(self) -> Dict[str, Any]:
        """加载设置"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return self.default_settings.copy()

    def save_settings(self):
        """保存设置"""
        os.makedirs(self.settings_dir, exist_ok=True)
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        """获取设置值"""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            value = value.get(k, {})
        return value if value != {} else default

    def set(self, key: str, value: Any):
        """设置值"""
        keys = key.split('.')
        settings = self.settings
        for k in keys[:-1]:
            if k not in settings:
                settings[k] = {}
            settings = settings[k]
        settings[keys[-1]] = value
        self.save_settings()