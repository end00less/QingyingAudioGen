import requests
import os
import json
from typing import Optional, List, Dict
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import tempfile


class TTSEngine:
    def __init__(self, base_url: str):
        """
        初始化 TTS 引擎
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.timeout = 30

    def synthesize(
            self,
            text: str,
            filename: str,
            emo_text: Optional[str] = None,
            emo_vector: Optional[List[float]] = None,
            save_path: Optional[str] = None,
            progress_callback=None
    ) -> str:
        """
        语音合成 - 支持进度回调
        """
        url = f"{self.base_url}/v2/synthesize"

        payload = {"text": text, "audio_path": filename}

        if emo_vector is not None:
            payload["emo_vector"] = emo_vector
        elif emo_text:
            payload["emo_text"] = emo_text

        try:
            if progress_callback:
                progress_callback(10, "开始合成...")

            response = self.session.post(url, json=payload, stream=True)
            response.raise_for_status()

            if progress_callback:
                progress_callback(50, "下载音频数据...")

            # 保存音频文件
            if save_path:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                if progress_callback:
                    progress_callback(100, "合成完成")

                return save_path
            else:
                # 返回临时文件路径
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                with open(temp_file.name, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                if progress_callback:
                    progress_callback(100, "合成完成")

                return temp_file.name

        except requests.exceptions.RequestException as e:
            raise Exception(f"TTS合成失败: {str(e)}")

    def test_connection(self) -> bool:
        """测试TTS服务连接"""
        try:
            url = f"{self.base_url}/v1/models"
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False

    def get_voices(self) -> List[Dict]:
        """获取可用音色列表"""
        try:
            url = f"{self.base_url}/v1/models"
            response = self.session.get(url)
            if response.status_code == 200:
                return response.json().get('voices', [])
            return []
        except:
            return []


class TTSProgressDialog:
    """TTS进度对话框"""

    def __init__(self, parent, title="语音合成"):
        self.parent = parent
        self.setup_dialog(title)

    def setup_dialog(self, title):
        """设置进度对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # 防止窗口被关闭
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 进度标签
        self.status_var = tk.StringVar(value="准备中...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, pady=(0, 10))

        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # 取消按钮
        self.cancel_btn = ttk.Button(main_frame, text="取消", command=self.cancel)
        self.cancel_btn.pack()

        self.is_cancelled = False

    def update_progress(self, percent: int, status: str):
        """更新进度"""
        if not self.is_cancelled:
            self.progress['value'] = percent
            self.status_var.set(status)
            self.dialog.update()

    def cancel(self):
        """取消操作"""
        self.is_cancelled = True
        self.status_var.set("取消中...")
        self.cancel_btn.config(state='disabled')

    def close(self):
        """关闭对话框"""
        self.dialog.destroy()


class TTSConfigDialog:
    """TTS配置对话框"""

    def __init__(self, parent, tts_engine: TTSEngine):
        self.tts_engine = tts_engine
        self.parent = parent
        self.result = None

        self.setup_dialog()

    def setup_dialog(self):
        """设置配置对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("TTS配置测试")
        self.dialog.geometry("500x400")
        self.dialog.transient(self.parent)

        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 连接测试
        test_frame = ttk.LabelFrame(main_frame, text="连接测试", padding="10")
        test_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(test_frame, text="测试连接", command=self.test_connection).pack(anchor=tk.W)
        self.connection_status = ttk.Label(test_frame, text="未测试")
        self.connection_status.pack(anchor=tk.W, pady=(5, 0))

        # 音色列表
        voice_frame = ttk.LabelFrame(main_frame, text="可用音色", padding="10")
        voice_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.voice_listbox = tk.Listbox(voice_frame, height=8)
        self.voice_listbox.pack(fill=tk.BOTH, expand=True)

        ttk.Button(voice_frame, text="刷新音色列表", command=self.refresh_voices).pack(anchor=tk.W, pady=(5, 0))

        # 测试合成
        synth_frame = ttk.LabelFrame(main_frame, text="测试合成", padding="10")
        synth_frame.pack(fill=tk.X)

        ttk.Label(synth_frame, text="测试文本:").pack(anchor=tk.W)
        self.test_text = tk.Text(synth_frame, height=3, width=50)
        self.test_text.pack(fill=tk.X, pady=(5, 10))
        self.test_text.insert(1.0, "这是一个TTS合成测试。")

        ttk.Button(synth_frame, text="测试合成", command=self.test_synthesis).pack(anchor=tk.W)

    def test_connection(self):
        """测试连接"""

        def run_test():
            try:
                if self.tts_engine.test_connection():
                    self.connection_status.config(text="连接成功", foreground="green")
                else:
                    self.connection_status.config(text="连接失败", foreground="red")
            except Exception as e:
                self.connection_status.config(text=f"连接错误: {str(e)}", foreground="red")

        threading.Thread(target=run_test, daemon=True).start()

    def refresh_voices(self):
        """刷新音色列表"""

        def get_voices():
            try:
                voices = self.tts_engine.get_voices()
                self.voice_listbox.delete(0, tk.END)
                for voice in voices:
                    self.voice_listbox.insert(tk.END, f"{voice.get('name', '未知')} - {voice.get('language', '')}")
            except Exception as e:
                messagebox.showerror("错误", f"获取音色列表失败: {str(e)}")

        threading.Thread(target=get_voices, daemon=True).start()

    def test_synthesis(self):
        """测试合成"""
        text = self.test_text.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("警告", "请输入测试文本")
            return

        # 选择音色
        selection = self.voice_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请先选择一个音色")
            return

        voice_name = self.voice_listbox.get(selection[0]).split(" - ")[0]

        # 显示进度对话框
        progress_dialog = TTSProgressDialog(self.dialog, "测试合成")

        def synthesize():
            try:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")

                def progress_callback(percent, status):
                    progress_dialog.update_progress(percent, status)

                # 合成语音
                audio_path = self.tts_engine.synthesize(
                    text=text,
                    filename=voice_name,
                    save_path=temp_file.name,
                    progress_callback=progress_callback
                )

                progress_dialog.close()

                # 询问是否播放
                if messagebox.askyesno("成功", "合成完成，是否播放？"):
                    # 播放音频
                    import subprocess
                    if os.name == 'nt':  # Windows
                        os.startfile(audio_path)
                    else:  # Linux/Mac
                        subprocess.run(['xdg-open', audio_path])

                # 清理临时文件
                try:
                    os.unlink(audio_path)
                except:
                    pass

            except Exception as e:
                progress_dialog.close()
                messagebox.showerror("错误", f"合成失败: {str(e)}")

        threading.Thread(target=synthesize, daemon=True).start()