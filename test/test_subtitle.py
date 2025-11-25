# test_subtitle.py
import sys
import os

sys.path.append(os.path.dirname(__file__))

from app.core.subtitle import subtitle_engine


def test_subtitle_generation():
    """测试字幕生成功能"""
    test_audio = """C:\\Users\\黄\\Documents\\2222\\3\\3\\audio\\1_凯特将军一惊急忙操.wav"""  # 替换为实际的测试音频文件
    output_srt = "test_output.srt"

    print(f"测试音频文件: {test_audio}")
    print(f"音频文件存在: {os.path.exists(test_audio)}")

    try:
        print("开始生成字幕...")
        result = subtitle_engine.generate_subtitle(test_audio, output_srt)
        print("字幕生成成功!")
        print(f"输出文件: {output_srt}")
        print(f"输出文件存在: {os.path.exists(output_srt)}")
        return True
    except Exception as e:
        print(f"字幕生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_subtitle_generation()