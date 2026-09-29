# -*- coding: utf-8 -*-
"""
nlp_utils.py
------------
Các hàm xử lý văn bản tiếng Việt dùng chung cho cả 3 phần:
  - Phần 1 (mô phỏng), Phần 2 (tóm tắt), Phần 3 (thử nghiệm).
"""

import os
import re

from underthesea import word_tokenize

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOPWORDS_PATH = os.path.join(BASE_DIR, "data", "stopwords_vi.txt")

SENTENCE_SPLIT_RE = re.compile(r"(?<=[\.\!\?…])\s+")
TOKEN_CLEAN_RE = re.compile(r"[^0-9a-zA-ZÀ-ỹà-ỹ_\s]")


def load_stopwords(path: str = STOPWORDS_PATH) -> set:
    """
    Nạp stopword từ file txt (mỗi dòng 1 từ/cụm từ).
    Các danh sách công khai (vd stopwords/vietnamese-stopwords) có từ ghép
    viết cách bằng khoảng trắng ("ít hơn"), trong khi underthesea xuất
    "ít_hơn" -> đổi khoảng trắng thành "_" để khớp.
    """
    with open(path, encoding="utf-8") as f:
        return {
            line.strip().lower().replace(" ", "_")
            for line in f if line.strip()
        }


STOPWORDS = load_stopwords()


def normalize_text(text: str) -> str:
    """
    Chuẩn hoá văn bản thô. Một số bộ dữ liệu (vd Vietnews) có thể đã được
    tách từ sẵn bằng dấu "_" -> thay bằng khoảng trắng để underthesea tách
    lại nhất quán, rồi gộp khoảng trắng thừa.
    """
    if not text:
        return ""
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> list:
    """Tách văn bản thành danh sách câu, giữ nguyên thứ tự gốc."""
    text = text.replace("\n", " ").strip()
    sentences = SENTENCE_SPLIT_RE.split(text)
    return [s.strip() for s in sentences if len(s.strip()) > 0]


def tokenize_and_clean(text: str, stopwords: set = STOPWORDS) -> list:
    """Tách từ (underthesea) rồi bỏ stopword, số, ký tự đặc biệt, từ quá ngắn."""
    tokens = word_tokenize(text.lower(), format="text").split()
    cleaned = []
    for tok in tokens:
        tok = TOKEN_CLEAN_RE.sub("", tok).strip("_")
        if not tok or tok in stopwords or len(tok) < 2:
            continue
        cleaned.append(tok)
    return cleaned


def simple_word_tokenize(text: str) -> list:
    """Tokenize thô (giữ stopword) dùng riêng cho ROUGE."""
    tokens = word_tokenize(text.lower(), format="text").split()
    out = [TOKEN_CLEAN_RE.sub("", t).strip("_") for t in tokens if t.strip()]
    return [t for t in out if t]
