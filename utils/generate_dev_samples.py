# app/utils/generate_dev_samples.py
import os
import edge_tts
import asyncio

# 扩展的语音配置 - 覆盖更多声音类型
DEV_VOICES = [
    # 男性声音系列
    {"name": "小行", "edge_voice": "zh-CN-YunxiNeural", "gender": "男", "desc": "温和的青年男声", "age": "青年"},
    {"name": "小阳", "edge_voice": "zh-CN-YunyangNeural", "gender": "男", "desc": "沉稳的成年男声", "age": "成年"},
    {"name": "小东", "edge_voice": "zh-CN-YunjianNeural", "gender": "男", "desc": "磁性的男声", "age": "成年"},
    {"name": "小辰", "edge_voice": "zh-CN-YunxiaNeural", "gender": "男", "desc": "温暖的男声", "age": "青年"},
    {"name": "小浩", "edge_voice": "zh-CN-YunzeNeural", "gender": "男", "desc": "阳光的男声", "age": "青年"},

    # 女性声音系列
    {"name": "小晓", "edge_voice": "zh-CN-XiaoxiaoNeural", "gender": "女", "desc": "甜美的少女音", "age": "少女"},
    {"name": "小夏", "edge_voice": "zh-CN-XiaoyiNeural", "gender": "女", "desc": "活泼的女声", "age": "青年"},
    {"name": "小倩", "edge_voice": "zh-CN-XiaobeiNeural", "gender": "女", "desc": "温柔的女声", "age": "成年"},
    {"name": "小芳", "edge_voice": "zh-CN-XiaomengNeural", "gender": "女", "desc": "可爱的女声", "age": "少女"},
    {"name": "小琳", "edge_voice": "zh-CN-XiaoqiuNeural", "gender": "女", "desc": "知性的女声", "age": "成年"},

    # 特色声音系列
    {"name": "小睿", "edge_voice": "zh-CN-YunxiNeural", "gender": "男", "desc": "睿智的解说音", "age": "成年", "style": "解说"},
    {"name": "小悦", "edge_voice": "zh-CN-XiaoxiaoNeural", "gender": "女", "desc": "愉悦的播报音", "age": "青年", "style": "播报"},
    {"name": "小威", "edge_voice": "zh-CN-YunyangNeural", "gender": "男", "desc": "威严的旁白", "age": "成年", "style": "旁白"},
    {"name": "小柔", "edge_voice": "zh-CN-XiaoyiNeural", "gender": "女", "desc": "柔和的叙述音", "age": "青年", "style": "叙述"},

    # 角色化声音系列
    {"name": "小龙", "edge_voice": "zh-CN-YunxiNeural", "gender": "男", "desc": "少年英雄音色", "age": "少年", "role": "英雄"},
    {"name": "小玉", "edge_voice": "zh-CN-XiaoxiaoNeural", "gender": "女", "desc": "仙女般音色", "age": "少女", "role": "仙女"},
    {"name": "老陈", "edge_voice": "zh-CN-YunyangNeural", "gender": "男", "desc": "长者音色", "age": "老年", "role": "长者"},
    {"name": "小宝", "edge_voice": "zh-CN-XiaoyiNeural", "gender": "女", "desc": "孩童音色", "age": "儿童", "role": "孩童"},

    # 情感化声音系列
    {"name": "小欢", "edge_voice": "zh-CN-XiaoxiaoNeural", "gender": "女", "desc": "欢快活泼音色", "age": "青年", "emotion": "欢快"},
    {"name": "小静", "edge_voice": "zh-CN-XiaobeiNeural", "gender": "女", "desc": "安静温柔音色", "age": "青年", "emotion": "温柔"},
    {"name": "小刚", "edge_voice": "zh-CN-YunxiNeural", "gender": "男", "desc": "刚毅坚定音色", "age": "成年", "emotion": "坚定"},
    {"name": "小默", "edge_voice": "zh-CN-YunyangNeural", "gender": "男", "desc": "沉稳内敛音色", "age": "成年", "emotion": "沉稳"},
]

# 多样化的样本文本
SAMPLE_TEXTS = [
    # 基础问候
    "你好，欢迎使用清影配音软件。",
    "很高兴为您服务。",
    "这是一个语音测试样本。",

    # 日常对话
    "今天天气真不错，阳光明媚。",
    "我喜欢阅读和听音乐。",
    "人工智能技术发展得真快。",

    # 情感表达
    "这真是个令人兴奋的消息！",
    "我对此感到非常满意。",
    "请不要担心，一切都会好起来的。",

    # 叙述性文本
    "在遥远的古代，有一个美丽的传说。",
    "科学技术是第一生产力。",
    "学习是人类进步的阶梯。",

    # 角色对话
    "我一定会完成这个任务的！",
    "这个世界需要更多的爱与和平。",
    "相信我，我们能够克服困难。",

    # 专业场景
    "接下来为您播报重要通知。",
    "本次会议到此结束，谢谢大家。",
    "系统初始化完成，准备就绪。",
]

# 多情绪样本（用于多情绪音色）
EMOTION_TEXTS = {
    "happy": [
        "太棒了！我简直不敢相信！",
        "今天是我最开心的一天！",
        "这真是个惊喜，我太高兴了！"
    ],
    "sad": [
        "听到这个消息我很难过。",
        "为什么会这样，我感到很伤心。",
        "这真让人失望。"
    ],
    "angry": [
        "我简直要气疯了！",
        "这太让人愤怒了！",
        "我无法接受这样的结果！"
    ],
    "calm": [
        "请保持冷静，慢慢说。",
        "一切都在掌控之中。",
        "我们需要理性地分析问题。"
    ]
}


async def generate_voice_sample(text, voice_config, output_file, emotion=None):
    """生成单个语音样本"""
    try:
        communicate = edge_tts.Communicate(text, voice_config["edge_voice"])
        await communicate.save(output_file)
        print(f"✅ 生成: {output_file}")
        return True
    except Exception as e:
        print(f"❌ 生成失败 {output_file}: {e}")
        return False


async def generate_standard_samples():
    """生成标准语音样本"""
    os.makedirs("dev_samples", exist_ok=True)

    print("开始生成开发语音样本...")
    print(f"共计 {len(DEV_VOICES)} 种音色，每种 {len(SAMPLE_TEXTS)} 个样本")

    success_count = 0
    total_count = len(DEV_VOICES) * len(SAMPLE_TEXTS)

    for voice_config in DEV_VOICES:
        voice_name = voice_config["name"]

        print(f"\n🎯 正在生成 [{voice_name}] 的样本...")

        # 为每个音色生成多个样本
        for i, text in enumerate(SAMPLE_TEXTS):
            output_file = f"dev_samples/{voice_name}_sample_{i + 1:02d}.wav"
            success = await generate_voice_sample(text, voice_config, output_file)
            if success:
                success_count += 1

    print(f"\n🎉 样本生成完成!")
    print(f"成功: {success_count}/{total_count}")
    return success_count


async def generate_emotion_samples():
    """为多情绪音色生成情感样本"""
    print("\n🎭 生成多情绪样本...")

    # 选择几个音色作为多情绪音色示例
    emotion_voices = [
                         voice for voice in DEV_VOICES
                         if voice.get("emotion") or voice.get("role")
                     ][:4]  # 取前4个

    for voice_config in emotion_voices:
        voice_name = voice_config["name"]
        emotion_dir = f"dev_samples/emotions/{voice_name}"
        os.makedirs(emotion_dir, exist_ok=True)

        print(f"\n🎭 生成 [{voice_name}] 的情绪样本...")

        for emotion, texts in EMOTION_TEXTS.items():
            for i, text in enumerate(texts):
                output_file = f"{emotion_dir}/{emotion}_{i + 1}.wav"
                await generate_voice_sample(text, voice_config, output_file)


def create_voice_metadata():
    """创建音色元数据文件"""
    metadata = []
    for voice in DEV_VOICES:
        voice_info = {
            "name": voice["name"],
            "description": voice["desc"],
            "gender": voice["gender"],
            "age": voice["age"],
            "style": voice.get("style", "通用"),
            "role": voice.get("role", ""),
            "emotion": voice.get("emotion", ""),
            "samples": [f"{voice['name']}_sample_{i + 1:02d}.wav" for i in range(len(SAMPLE_TEXTS))]
        }
        metadata.append(voice_info)

    import json
    with open("dev_samples/voice_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print("✅ 音色元数据已生成: dev_samples/voice_metadata.json")


async def main():
    """主函数"""
    print("🚀 清影配音软件 - 开发语音样本生成器")
    print("=" * 50)

    # 生成标准样本
    await generate_standard_samples()

    # 生成情绪样本
    await generate_emotion_samples()

    # 创建元数据
    create_voice_metadata()

    print("\n🎊 所有样本生成完成！")
    print("📁 样本保存在: dev_samples/ 目录")
    print("📋 元数据文件: dev_samples/voice_metadata.json")


if __name__ == "__main__":
    asyncio.run(main())
