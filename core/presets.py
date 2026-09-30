# -*- coding: utf-8 -*-
"""
core/presets.py
---------------
Các bộ dữ liệu mẫu (preset) cho giao diện tóm tắt (Phần 1+).
Gồm preset 'toy' (8 câu, 2 chủ đề rõ rệt) và 'ev' (đoạn xe điện mẫu).
"""

from core.toy_data import TOY_SENTENCES
from core.sample_text import SAMPLE_TEXT_SUMMARIZE
from core.summarizer_pipeline import (
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    DEFAULT_ITERATIONS,
    DEFAULT_NUM_TOPICS,
    DEFAULT_SEED,
    DEFAULT_N_SENTENCES,
)


def _join(sentences):
    # BE-7: BẮT BUỘC có dấu chấm cuối câu để bộ tách câu nhận diện đủ 8 câu
    return " ".join(s.strip().rstrip(".") + "." for s in sentences)


PRESETS = {
    "toy": {
        "label": "Dữ liệu nhỏ: 8 câu, 2 chủ đề",
        "text": _join(TOY_SENTENCES),
        "params": {
            "K": 2,
            "iterations": 30,
            "alpha": 0.1,
            "beta": 0.01,
            "seed": 42,
            "n_sentences": 2,
        },
    },
    "ev": {
        "label": "Đoạn mẫu: xe điện",
        "text": SAMPLE_TEXT_SUMMARIZE,
        "params": {
            "K": DEFAULT_NUM_TOPICS,
            "iterations": DEFAULT_ITERATIONS,
            "alpha": DEFAULT_ALPHA,
            "beta": DEFAULT_BETA,
            "seed": DEFAULT_SEED,
            "n_sentences": DEFAULT_N_SENTENCES,
        },
    },
}
