# app/core/llm_engine.py
import json
import re
import time
import random
from openai import OpenAI
from app.core.prompts import get_auto_fix_json_prompt


class LLMEngine:
    def __init__(self, api_key: str, base_url: str, model_name: str, custom_params: str = None):
        """
        api_key: LLM API Key
        base_url: OpenAI-compatible API URL（例如企业版/自建 LLM）
        model_name: 模型名称
        custom_params: 自定义参数字符串
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")  # 去掉末尾斜杠
        self.model_name = model_name

        # 解析自定义参数
        self.custom_params = {}
        if custom_params:
            try:
                if isinstance(custom_params, str):
                    self.custom_params = json.loads(custom_params)
                else:
                    self.custom_params = custom_params

                if not isinstance(self.custom_params, dict):
                    self.custom_params = {}
            except (json.JSONDecodeError, TypeError):
                self.custom_params = {}

        # 初始化 OpenAI 客户端
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url
        )

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
            # 构建请求参数
            request_params = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "timeout": 30.0,  # 30秒超时
            }

            # 合并自定义参数
            request_params.update(self.custom_params)

            response = self.client.chat.completions.create(**request_params)
            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"LLM测试失败: {str(e)}")

    def generate_text(self, prompt: str, retries: int = 3, delay: float = 1.0) -> str:
        """
        流式生成：边生成边输出
        """
        for attempt in range(retries):
            try:
                # 构建请求参数
                request_params = {
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "timeout": 300.0,  # 5分钟超时
                }

                # 合并自定义参数
                request_params.update(self.custom_params)

                # 流式响应
                response = self.client.chat.completions.create(**request_params)

                # 拼接内容
                full_text = ""
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)  # 实时输出
                        full_text += content

                print("\n--- 输出完成 ---")
                return full_text

            except Exception as e:
                if attempt < retries - 1:
                    sleep_time = delay * (2 ** attempt) + random.random()
                    print(f"第{attempt + 1}次尝试失败，{sleep_time:.2f}秒后重试...")
                    time.sleep(sleep_time)
                else:
                    raise Exception(f"LLM调用失败: {str(e)}")

    def generate_smart_text(self, prompt: str) -> str:
        """
        智能文本生成（非流式）
        """
        try:
            # 构建请求参数
            request_params = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "timeout": 300.0,  # 5分钟超时
            }

            # 合并自定义参数
            request_params.update(self.custom_params)

            response = self.client.chat.completions.create(**request_params)
            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"智能文本生成失败: {str(e)}")

    def generate_smart_text_stream(self, prompt: str) -> str:
        """
        智能文本生成（流式）
        """
        try:
            # 构建请求参数
            request_params = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
                "timeout": 300.0,  # 5分钟超时
            }

            # 合并自定义参数
            request_params.update(self.custom_params)

            response = self.client.chat.completions.create(**request_params)

            # 拼接内容
            full_text = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)  # 实时输出
                    full_text += content

            print("\n--- 输出完成 ---")
            return full_text

        except Exception as e:
            raise Exception(f"智能文本流式生成失败: {str(e)}")

    # json输出问题解决
    def save_load_json(self, json_str: str):
        """解析JSON，如果失败则尝试修复"""
        # 先尝试直接加载json
        try:
            json_obj = json.loads(json_str)
            return json_obj
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}，尝试修复")
            try:
                # 尝试修复JSON
                prompt = get_auto_fix_json_prompt(json_str)
                res = self.generate_text(prompt)

                # 提取<result>标签内容
                cleaned_res = self._extract_result_tag(res)
                return json.loads(cleaned_res)

            except Exception as fix_error:
                print(f"JSON修复失败: {fix_error}")
                raise Exception(f"JSON解析和修复都失败: {str(fix_error)}")


def main():
    # 测试配置
    api_key = "sk-89c8b48798b6422fa8e9b59664dabf1e"
    api_url = "https://api.deepseek.com"
    model_name = "deepseek-reasoner"

    llm = LLMEngine(api_key, api_url, model_name)

    # 测试 prompt
    prompt = "输出<result>标签的结果，例如：<result>这是测试内容</result>。问题：你好，请问你是谁"

    try:
        # 测试非流式
        print("=== 测试非流式生成 ===")
        result = llm.generate_text_test(prompt)
        print("LLM 返回结果:", result)

        # 测试流式
        print("\n=== 测试流式生成 ===")
        result_stream = llm.generate_text(prompt)
        print("LLM 流式返回结果:", result_stream)

    except Exception as e:
        print("调用 LLM 出错：", e)


if __name__ == "__main__":
    main()