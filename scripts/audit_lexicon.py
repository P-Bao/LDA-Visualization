# -*- coding: utf-8 -*-
"""
scripts/audit_lexicon.py
------------------------
Kiem toan stopword don am tiet: tim bigram (S, x) hoac (x, S) trong corpus
ma x KHONG phai stopword va bigram chua nam trong COMPOUND_SET.

Ket qua giup nguoi duyet quyet dinh:
  - Co nen xoa S khoi STOPWORDS khong?
  - Hay can them bigram tuong ung vao COMPOUND_WORDS?

Chay: python scripts/audit_lexicon.py
"""

import sys
import os
import json
import re
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")  # Windows: in tieng Viet dung
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from core.vi_lexicon import STOPWORDS, COMPOUND_SET, is_stopword
from core.summarizer_preprocess import TOKEN_SPLIT_RE


# ---------------------------------------------------------------------------
# Nap corpus
# ---------------------------------------------------------------------------

def _load_corpus():
    texts = []

    # 1. sample_dataset.json
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sample_dataset.json")
    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            dataset = json.load(f)
        if isinstance(dataset, list):
            for item in dataset:
                if isinstance(item, dict) and "content" in item:
                    texts.append(item["content"])
        elif isinstance(dataset, dict):
            for v in dataset.values():
                if isinstance(v, str):
                    texts.append(v)
                elif isinstance(v, dict) and "content" in v:
                    texts.append(v["content"])

    # 2. TOY_SENTENCES
    try:
        from core.toy_data import TOY_SENTENCES
        texts.extend(TOY_SENTENCES)
    except ImportError:
        pass

    # 3. SAMPLE_TEXT_SUMMARIZE
    try:
        from core.sample_text import SAMPLE_TEXT_SUMMARIZE
        texts.append(SAMPLE_TEXT_SUMMARIZE)
    except ImportError:
        pass

    return texts


# ---------------------------------------------------------------------------
# Trich bigram
# ---------------------------------------------------------------------------

def _get_bigrams(text):
    words = TOKEN_SPLIT_RE.findall(text.lower())
    return list(zip(words, words[1:]))


# ---------------------------------------------------------------------------
# Audit chinh
# ---------------------------------------------------------------------------

def audit():
    texts = _load_corpus()
    print(f"Corpus: {len(texts)} doan van duoc nap.\n")

    # Chi xet stopword don am tiet (khong dau cach)
    single_stops = {s for s in STOPWORDS if " " not in s}

    bigram_counter = Counter()
    for text in texts:
        for a, b in _get_bigrams(text):
            bigram_counter[(a, b)] += 1

    # Tap ket qua: bigram co chua stopword don + am tiet noi dung + chua la compound
    suspicious = []  # (stopword, partner, position, count, bigram_str)
    for (a, b), count in bigram_counter.items():
        bigram_str = a + " " + b
        if bigram_str in COMPOUND_SET:
            continue  # da duoc xu ly dung
        if a in single_stops and not is_stopword(b) and b.isalpha():
            suspicious.append((a, b, "prefix", count, bigram_str))
        elif b in single_stops and not is_stopword(a) and a.isalpha():
            suspicious.append((b, a, "suffix", count, bigram_str))

    # Sap xep theo stopword, roi theo so lan xuat hien
    suspicious.sort(key=lambda x: (x[0], -x[3]))

    if not suspicious:
        print("OK Khong tim thay bigram dang ngo -- tu dien va stopword nhat quan.")
        return

    print("=" * 72)
    print(f"{'Stopword':<10} {'Vi tri':<8} {'Bigram':<30} {'So lan'}")
    print("=" * 72)
    prev_stop = None
    for stop, partner, pos, count, bigram_str in suspicious:
        if stop != prev_stop:
            print(f"\n--- stopword: '{stop}' ---")
            prev_stop = stop
        pos_label = "truoc" if pos == "prefix" else "sau"
        print(f"  {stop:<10} {pos_label:<8} {bigram_str:<30} {count:>4} lan")

    print("\n" + "=" * 72)
    print(f"Tong cong: {len(suspicious)} bigram can xem xet.")
    print("Hanh dong goi y:")
    print("  - Them bigram vao COMPOUND_WORDS trong vi_lexicon.py (neu la tu noi dung).")
    print("  - Hoac xoa stopword khoi STOPWORDS neu no thuong xuyen la tu noi dung.")


if __name__ == "__main__":
    audit()
