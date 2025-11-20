# config/app_config.py
import os
import configparser
from pathlib import Path


class AppConfig:
    def __init__(self, config_file="config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(self.config_file):
            self.create_default_config()

        self.config.read(self.config_file, encoding='utf-8')

    def create_default_config(self):
        """创建默认配置文件"""
        # 获取项目根目录
        project_root = Path(__file__).parent.parent

        self.config['PATHS'] = {
            'project_root': str(project_root),
            'samples_dir': str(project_root / "dev_samples"),
            'logs_dir': str(project_root / "logs"),
            'temp_dir': str(project_root / "temp")
        }

        self.config['VOICES'] = {
            'default_tts_provider': '1',
            'auto_init_default_voices': 'true'
        }

        self.config['DEFAULT_VOICES'] = {
            '小行': '小行_sample_01.wav',
            '小晓': '小晓_sample_01.wav',
            '小阳': '小阳_sample_01.wav',
            '小夏': '小夏_sample_01.wav',
            '小东': '小东_sample_01.wav',
            '小倩': '小倩_sample_01.wav',
            '小睿': '小睿_sample_01.wav',
            '小悦': '小悦_sample_01.wav',
            '小龙': '小龙_sample_01.wav',
            '小玉': '小玉_sample_01.wav',
            '老陈': '老陈_sample_01.wav',
            '小欢': '小欢_sample_01.wav',
            '小静': '小静_sample_01.wav'
        }

        # 保存配置文件
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)

        print(f"✅ 创建默认配置文件: {self.config_file}")

    def get_samples_dir(self):
        """获取样本目录的绝对路径"""
        samples_dir = self.config.get('PATHS', 'samples_dir', fallback='')
        if not samples_dir:
            # 默认路径
            project_root = Path(__file__).parent.parent
            samples_dir = str(project_root / "dev_samples")
        return samples_dir

    def get_voice_sample_path(self, voice_name):
        """获取音色样本的绝对路径"""
        samples_dir = self.get_samples_dir()
        sample_file = self.config.get('DEFAULT_VOICES', voice_name, fallback='')

        if sample_file:
            return os.path.join(samples_dir, sample_file)
        else:
            return ""

    def get_default_tts_provider_id(self):
        """获取默认TTS服务商ID"""
        return int(self.config.get('VOICES', 'default_tts_provider', fallback='1'))

    def should_auto_init_voices(self):
        """是否自动初始化默认音色"""
        return self.config.getboolean('VOICES', 'auto_init_default_voices', fallback=True)


# 全局配置实例
app_config = AppConfig()