import re
import json
import difflib
from typing import List, Dict, Tuple, Optional
import tkinter as tk
from tkinter import ttk, scrolledtext
from pypinyin import lazy_pinyin


class TextCorrectorFinal:
    def __init__(self):
        self.correction_history = []

    def clean_text(self, text: str) -> str:
        """清理文本"""
        text = re.sub(r'[\n\r\u3000]', '', text)
        text = re.sub(r'[""「」『』]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def split_sentences(self, text: str) -> List[str]:
        """分句处理"""
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        text = text.replace('\u3000', ' ').strip()

        sentences = re.split(r'([。！？!?：；]|(?<!\d)\.(?!\d)|\n+)', text)
        result = []
        current_sentence = ""

        for part in sentences:
            if not part:
                continue
            current_sentence += part

            if re.fullmatch(r'[。！？!?：；]', part) or part == '.' or re.fullmatch(r'\n+', part):
                if part == '.':
                    if self._looks_like_abbreviation(current_sentence):
                        continue

                sent = current_sentence.strip()
                if re.fullmatch(r'\n+', part):
                    sent = re.sub(r'\n+$', '', sent).strip()

                if sent and not re.fullmatch(r'^[\W_]+$', sent):
                    result.append(sent)

                current_sentence = ""

        tail = current_sentence.strip()
        if tail and not re.fullmatch(r'^[\W_]+$', tail):
            result.append(tail)

        return result

    def _looks_like_abbreviation(self, sentence_with_dot: str) -> bool:
        """判断是否为缩写"""
        s = sentence_with_dot.rstrip()
        m = re.search(r'([A-Za-z0-9\.]+)\.$', s)
        if not m:
            return False

        token = m.group(1)
        if re.fullmatch(r'[A-Za-z]{1,4}', token) and token[0].isupper():
            return True
        if re.fullmatch(r'[A-Za-z](?:\.[A-Za-z]){2,}', token):
            return True

        return False

    def correct_ai_text(self, original_text: str, ai_data: List[Dict]) -> List[Dict]:
        """校正AI文本"""
        original_sentences = self.split_sentences(original_text)
        corrected_data = []
        used_original_indices = set()
        current_original_index = 0

        for ai_item in ai_data:
            ai_text = ai_item.get('text_content', '')
            ai_sentences = self.split_sentences(ai_text)
            corrected_sentences_for_item = []

            for ai_sentence in ai_sentences:
                match_index, similarity = self.find_best_sentence_match(
                    ai_sentence, original_sentences, current_original_index
                )

                if match_index is not None:
                    original_match = original_sentences[match_index]
                    corrected_sentences_for_item.append(original_match)
                    used_original_indices.add(match_index)
                    current_original_index = match_index + 1

                    # 记录校正历史
                    self.correction_history.append({
                        'ai_sentence': ai_sentence,
                        'original_sentence': original_match,
                        'similarity': similarity
                    })
                else:
                    corrected_sentences_for_item.append(ai_sentence)

            corrected_text = self.clean_text(" ".join(corrected_sentences_for_item))
            if corrected_text:
                corrected_item = ai_item.copy()
                corrected_item['text_content'] = corrected_text
                corrected_data.append(corrected_item)

        return corrected_data

    def find_best_sentence_match(self, ai_sentence: str, original_sentences: List[str],
                                 start_index: int = 0, threshold: float = 0.6) -> Tuple[Optional[int], float]:
        """查找最佳匹配句子"""
        processed_ai_sentence = self.clean_text(ai_sentence)
        if not processed_ai_sentence:
            return None, 0

        best_match_index = None
        best_similarity = 0
        search_window = 20

        for i in range(start_index, min(start_index + search_window, len(original_sentences))):
            original_sentence = original_sentences[i]
            processed_original_sentence = self.clean_text(original_sentence)

            if not processed_original_sentence:
                continue

            matcher = difflib.SequenceMatcher(None, processed_ai_sentence, processed_original_sentence)
            similarity = matcher.ratio()

            if similarity > best_similarity:
                best_similarity = similarity
                best_match_index = i

        if best_similarity < threshold:
            return None, best_similarity

        return best_match_index, best_similarity


class TextCorrectionDialog:
    """文本校正对话框"""

    def __init__(self, parent, original_text: str, ai_text: str):
        self.parent = parent
        self.original_text = original_text
        self.ai_text = ai_text
        self.corrector = TextCorrectorFinal()
        self.corrected_data = None

        self.setup_dialog()
        self.load_texts()

    def setup_dialog(self):
        """设置校正对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("文本校正")
        self.dialog.geometry("800x600")
        self.dialog.transient(self.parent)

        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建笔记本控件
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 原文标签页
        original_frame = ttk.Frame(notebook, padding="10")
        notebook.add(original_frame, text="原文")

        ttk.Label(original_frame, text="原文内容:").pack(anchor=tk.W)
        self.original_text_widget = scrolledtext.ScrolledText(original_frame, height=15)
        self.original_text_widget.pack(fill=tk.BOTH, expand=True)

        # AI文本标签页
        ai_frame = ttk.Frame(notebook, padding="10")
        notebook.add(ai_frame, text="AI解析结果")

        ttk.Label(ai_frame, text="AI解析内容:").pack(anchor=tk.W)
        self.ai_text_widget = scrolledtext.ScrolledText(ai_frame, height=15)
        self.ai_text_widget.pack(fill=tk.BOTH, expand=True)

        # 校正结果标签页
        corrected_frame = ttk.Frame(notebook, padding="10")
        notebook.add(corrected_frame, text="校正结果")

        ttk.Label(corrected_frame, text="校正后内容:").pack(anchor=tk.W)
        self.corrected_text_widget = scrolledtext.ScrolledText(corrected_frame, height=15)
        self.corrected_text_widget.pack(fill=tk.BOTH, expand=True)

        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(btn_frame, text="开始校正", command=self.start_correction).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="应用结果", command=self.apply_correction).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy).pack(side=tk.LEFT)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(anchor=tk.W, pady=(5, 0))

    def load_texts(self):
        """加载文本内容"""
        self.original_text_widget.insert(1.0, self.original_text)
        self.ai_text_widget.insert(1.0, self.ai_text)

    def start_correction(self):
        """开始校正"""
        try:
            self.status_var.set("校正中...")

            # 解析AI文本为JSON
            ai_data = json.loads(self.ai_text)

            # 执行校正
            self.corrected_data = self.corrector.correct_ai_text(self.original_text, ai_data)

            # 显示校正结果
            self.corrected_text_widget.delete(1.0, tk.END)
            self.corrected_text_widget.insert(1.0, json.dumps(self.corrected_data, ensure_ascii=False, indent=2))

            # 显示校正统计
            total_corrections = len(self.corrector.correction_history)
            self.status_var.set(f"校正完成，共校正 {total_corrections} 处")

        except Exception as e:
            self.status_var.set(f"校正失败: {str(e)}")
            tk.messagebox.showerror("错误", f"校正失败: {str(e)}")

    def apply_correction(self):
        """应用校正结果"""
        if self.corrected_data is None:
            tk.messagebox.showwarning("警告", "请先执行校正")
            return

        self.dialog.destroy()

    def get_corrected_data(self):
        """获取校正后的数据"""
        return self.corrected_data