import json
import re
import time
import random
import openai
from typing import Optional, Dict, Any
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading


class LLMEngine:
    def __init__(self, api_key: str, base_url: str, model_name: str, custom_params: str = None):
        """
        LLM引擎 - 桌面版
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name

        # 解析自定义参数
        self.custom_params = {}
        if custom_params:
            try:
                self.custom_params = json.loads(custom_params)
            except:
                self.custom_params = {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2000
                }

        # 配置OpenAI客户端
        openai.api_key = api_key
        openai.api_base = self.base_url

    def _extract_result_tag(self, text: str) -> str:
        """提取 <result> 标签内容"""
        match = re.search(r"<result>(.*?)</result>", text, re.DOTALL)
        if not match:
            raise ValueError("Response does not contain <result>...</result> tag")
        return match.group(1).strip()

    def generate_text_test(self, prompt: str) -> str:
        """
        测试：生成结果并返回
        """
        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                timeout=30,
                **self.custom_params
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")

    def generate_text_stream(self, prompt: str, callback=None) -> str:
        """
        流式生成：边生成边通过回调输出
        """
        full_text = ""

        try:
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=True,
                timeout=300,
                **self.custom_params
            )

            for chunk in response:
                if 'choices' in chunk and 'delta' in chunk['choices'][0]:
                    content = chunk['choices'][0]['delta'].get('content')
                    if content:
                        full_text += content
                        if callback:
                            callback(content)

            return full_text

        except Exception as e:
            if callback:
                callback(f"\n[错误] LLM调用失败: {str(e)}\n")
            raise

    def save_load_json(self, json_str: str) -> Dict:
        """JSON解析和自动修复"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            print("JSON解析错误，尝试修复...")
            # 简单的JSON修复逻辑
            json_str = re.sub(r',\s*}', '}', json_str)
            json_str = re.sub(r',\s*]', ']', json_str)
            json_str = re.sub(r"'", '"', json_str)
            try:
                return json.loads(json_str)
            except:
                raise ValueError("JSON解析失败")


class LLMTestDialog:
    """LLM测试对话框"""

    def __init__(self, parent, llm_engine: LLMEngine):
        self.llm_engine = llm_engine
        self.parent = parent

        self.setup_dialog()

    def setup_dialog(self):
        """设置测试对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("LLM服务测试")
        self.dialog.geometry("600x500")
        self.dialog.transient(self.parent)

        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 测试提示词
        ttk.Label(main_frame, text="测试提示词:").pack(anchor=tk.W, pady=(0, 5))
        self.prompt_text = scrolledtext.ScrolledText(main_frame, height=4, width=60)
        self.prompt_text.pack(fill=tk.X, pady=(0, 10))
        self.prompt_text.insert(1.0, "请用JSON格式输出一个简单的用户信息，包含name、age、city字段")

        # 测试按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(btn_frame, text="开始测试", command=self.start_test).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="清空结果", command=self.clear_output).pack(side=tk.LEFT)

        # 输出区域
        ttk.Label(main_frame, text="测试结果:").pack(anchor=tk.W, pady=(0, 5))
        self.output_text = scrolledtext.ScrolledText(main_frame, height=15, width=60)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, pady=(5, 0))

    def start_test(self):
        """开始测试"""
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            tk.messagebox.showwarning("警告", "请输入测试提示词")
            return

        self.status_var.set("测试中...")
        self.output_text.insert(tk.END, "=== 开始测试 ===\n")

        # 在新线程中执行测试
        thread = threading.Thread(target=self._run_test, args=(prompt,))
        thread.daemon = True
        thread.start()

    def _run_test(self, prompt: str):
        """执行测试"""
        try:
            def callback(content):
                self.output_text.insert(tk.END, content)
                self.output_text.see(tk.END)
                self.dialog.update()

            result = self.llm_engine.generate_text_stream(prompt, callback)

            self.output_text.insert(tk.END, f"\n\n=== 测试完成 ===\n")
            self.output_text.insert(tk.END, f"总字符数: {len(result)}\n")

            # 验证JSON格式
            try:
                json_data = self.llm_engine.save_load_json(result)
                self.output_text.insert(tk.END, f"JSON验证: 成功\n")
                self.output_text.insert(tk.END, f"JSON内容: {json.dumps(json_data, ensure_ascii=False, indent=2)}\n")
            except:
                self.output_text.insert(tk.END, f"JSON验证: 失败\n")

            self.status_var.set("测试完成")

        except Exception as e:
            self.output_text.insert(tk.END, f"\n[错误] {str(e)}\n")
            self.status_var.set("测试失败")

    def clear_output(self):
        """清空输出"""
        self.output_text.delete(1.0, tk.END)