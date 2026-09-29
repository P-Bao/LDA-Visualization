# -*- coding: utf-8 -*-
"""
dataset_loader.py
------------------
Nạp tập văn bản cho PHẦN 3. Mọi nguồn đều trả về CÙNG một định dạng:

    [{"id", "topic_label", "title", "content", "reference_summary"}, ...]

Nguồn hỗ trợ:
  - "sample"   : data/sample_dataset.json (10 bài tự viết, chạy offline)
  - "vietnews" : harouzie/vietnews trên Hugging Face
                 (cột: guid, title, abstract, article)
                 article  -> content
                 abstract -> reference_summary
"""

import json
import os
import random

from core.nlp_utils import normalize_text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_PATH = os.path.join(BASE_DIR, "data", "sample_dataset.json")
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")

HF_NAME = "harouzie/vietnews"


def load_bundled_sample(path: str = SAMPLE_PATH) -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _cache_path(split: str, limit: int, seed: int, min_sentences: int) -> str:
    return os.path.join(CACHE_DIR, f"vietnews_{split}_n{limit}_s{seed}_m{min_sentences}.json")


def load_vietnews(split: str = "test", limit: int = 100, seed: int = 42,
                  min_sentences: int = 4, max_chars: int = 6000,
                  use_cache: bool = True) -> list:
    """
    Nạp harouzie/vietnews (cần internet + `pip install datasets` ở lần đầu).

    - Lấy ngẫu nhiên `limit` bài (cố định theo `seed` để tái lập kết quả).
    - Bỏ bài quá ngắn (< min_sentences câu) hoặc quá dài (> max_chars ký tự)
      để LDA cấp-câu ổn định và thời gian chạy hợp lý.
    - Lưu cache JSON vào data/cache/ -> lần sau chạy offline được.
    """
    from core.nlp_utils import split_sentences

    cache = _cache_path(split, limit, seed, min_sentences)
    if use_cache and os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            return json.load(f)

    from datasets import load_dataset  # import trễ: chỉ cần khi thật sự tải

    ds = load_dataset(HF_NAME, split=split)
    indices = list(range(len(ds)))
    random.Random(seed).shuffle(indices)

    docs = []
    for idx in indices:
        row = ds[idx]
        article = normalize_text(row.get("article", ""))
        abstract = normalize_text(row.get("abstract", ""))
        if not article or not abstract:
            continue
        if len(article) > max_chars:
            continue
        if len(split_sentences(article)) < min_sentences:
            continue
        docs.append({
            "id": str(row.get("guid", idx)),
            "topic_label": "",
            "title": normalize_text(row.get("title", "")),
            "content": article,
            "reference_summary": abstract,
        })
        if len(docs) >= limit:
            break

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False)
    return docs


def load_dataset_by_source(source: str = "sample", limit: int = 100, split: str = "test",
                           seed: int = 42) -> list:
    if source == "vietnews":
        return load_vietnews(split=split, limit=limit, seed=seed)
    return load_bundled_sample()
