# app/ui/voice_dialog.py
import tkinter as tk
from tkinter import ttk
from typing import Optional

from app.entity.voice_entity import VoiceEntity


class VoiceDialog:
    def __init__(self, parent, tts_provider_id: int, app_controller, voice: Optional[VoiceEntity] = None):
        self.parent = parent
        self.tts_provider_id = tts_provider_id
        self.app_controller = app_controller
        self.voice = voice
        self.result = None

        self.setup_dialog()

    def setup_dialog(self):
        """设置对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("编辑音色" if self.voice else "新建音色")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() - self.dialog.winfo_width()) // 2
        y = (self.dialog.winfo_screenheight() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")

        self.create_widgets()

    def create_widgets(self):
        """创建控件"""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 音色名称
        ttk.Label(main_frame, text="音色名称:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.name_var = tk.StringVar()
        if self.voice:
            self.name_var.set(self.voice.name)
        self.name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        # 音色描述
        ttk.Label(main_frame, text="音色描述:").grid(row=1, column=0, sticky=tk.NW, pady=10)
        self.desc_text = tk.Text(main_frame, width=30, height=4)
        self.desc_text.grid(row=1, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        if self.voice and self.voice.description:
            self.desc_text.insert('1.0', self.voice.description)

        # 参考音频路径
        ttk.Label(main_frame, text="参考音频路径:").grid(row=2, column=0, sticky=tk.W, pady=10)
        self.ref_path_var = tk.StringVar()
        if self.voice:
            self.ref_path_var.set(self.voice.reference_path or "")
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=2, column=1, sticky=tk.W + tk.E, pady=10, padx=(10, 0))

        self.ref_path_entry = ttk.Entry(path_frame, textvariable=self.ref_path_var, width=25)
        self.ref_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(
            path_frame,
            text="浏览",
            command=self.browse_audio_file,
            width=8
        ).pack(side=tk.RIGHT, padx=(5, 0))

        # 多情绪音色
        self.multi_emotion_var = tk.BooleanVar()
        if self.voice:
            self.multi_emotion_var.set(self.voice.is_multi_emotion == 1)
        ttk.Checkbutton(
            main_frame,
            text="多情绪音色",
            variable=self.multi_emotion_var
        ).grid(row=3, column=1, sticky=tk.W, pady=10, padx=(10, 0))

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="保存", command=self.save_voice).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

    def browse_audio_file(self):
        """浏览音频文件"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="选择参考音频文件",
            filetypes=[("音频文件", "*.wav *.mp3 *.flac"), ("所有文件", "*.*")]
        )
        if filename:
            self.ref_path_var.set(filename)

    def save_voice(self):
        """保存音色"""
        name = self.name_var.get().strip()
        if not name:
            tk.messagebox.showerror("错误", "音色名称不能为空")
            return

        description = self.desc_text.get('1.0', tk.END).strip()
        reference_path = self.ref_path_var.get().strip() or None
        is_multi_emotion = 1 if self.multi_emotion_var.get() else 0

        try:
            if self.voice:
                # 更新现有音色
                update_data = {
                    'name': name,
                    'description': description,
                    'reference_path': reference_path,
                    'is_multi_emotion': is_multi_emotion
                }
                success = self.app_controller.voice_controller.update_voice(
                    self.voice.id,
                    **update_data
                )
            else:
                # 创建新音色
                voice = self.app_controller.voice_controller.create_voice(
                    tts_provider_id=self.tts_provider_id,
                    name=name,
                    reference_path=reference_path,
                    description=description,
                    is_multi_emotion=is_multi_emotion
                )
                success = voice is not None

            if success:
                self.result = True
                self.dialog.destroy()
            else:
                tk.messagebox.showerror("错误", "保存音色失败")

        except Exception as e:
            tk.messagebox.showerror("错误", f"保存音色失败: {str(e)}")