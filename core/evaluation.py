# -*- coding: utf-8 -*-
"""
evaluation.py
-------------
Đánh giá chất lượng bản tóm tắt trích xuất bằng ROUGE (tự cài đặt, không phụ
thuộc thư viện ngoài, để chạy offline không cần internet):
  - ROUGE-N (đếm trùng n-gram giữa bản tóm tắt máy tạo ra và bản tóm tắt tham chiếu)
  - ROUGE-L (dựa trên chuỗi con chung dài nhất - LCS)

Đây là bản triển khai ĐƠN GIẢN HOÁ nhằm mục đích minh hoạ/giảng dạy, không phải
bản sao chính xác của công cụ ROUGE gốc (pyrouge) — nhưng dùng cùng công thức
recall/precision/F1 chuẩn nên đủ để so sánh tương đối giữa các cấu hình mô hình.
"""

from collections import Counter

from core.nlp_utils import simple_word_tokenize


def _ngrams(tokens, n):
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def rouge_n(reference: str, hypothesis: str, n: int = 1):
    ref_tokens = simple_word_tokenize(reference)
    hyp_tokens = simple_word_tokenize(hypothesis)

    ref_ngrams = Counter(_ngrams(ref_tokens, n))
    hyp_ngrams = Counter(_ngrams(hyp_tokens, n))

    overlap = sum((ref_ngrams & hyp_ngrams).values())
    ref_count = sum(ref_ngrams.values())
    hyp_count = sum(hyp_ngrams.values())

    recall = overlap / ref_count if ref_count else 0.0
    precision = overlap / hyp_count if hyp_count else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"recall": recall, "precision": precision, "f1": f1}


def _lcs_length(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


def rouge_l(reference: str, hypothesis: str):
    ref_tokens = simple_word_tokenize(reference)
    hyp_tokens = simple_word_tokenize(hypothesis)
    lcs = _lcs_length(ref_tokens, hyp_tokens)

    recall = lcs / len(ref_tokens) if ref_tokens else 0.0
    precision = lcs / len(hyp_tokens) if hyp_tokens else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"recall": recall, "precision": precision, "f1": f1}


def evaluate_document(reference_summary: str, generated_summary: str):
    return {
        "rouge1": rouge_n(reference_summary, generated_summary, 1),
        "rouge2": rouge_n(reference_summary, generated_summary, 2),
        "rougeL": rouge_l(reference_summary, generated_summary),
    }


def average_scores(per_doc_results: list) -> dict:
    metrics = ["rouge1", "rouge2", "rougeL"]
    fields = ["recall", "precision", "f1"]
    avg = {m: {f: 0.0 for f in fields} for m in metrics}
    n = len(per_doc_results)
    if n == 0:
        return avg
    for res in per_doc_results:
        for m in metrics:
            for f in fields:
                avg[m][f] += res[m][f]
    for m in metrics:
        for f in fields:
            avg[m][f] = round(avg[m][f] / n, 4)
    return avg


# ---------------------------------------------------------------------------
# Baseline để so sánh với tóm tắt LDA
# ---------------------------------------------------------------------------
import random as _random

from core.nlp_utils import split_sentences as _split_sentences


def lead_k_summary(text: str, k: int = 3) -> str:
    """Baseline kinh điển: lấy k câu đầu tiên (rất mạnh với văn bản báo chí)."""
    return " ".join(_split_sentences(text)[:k])


def random_k_summary(text: str, k: int = 3, seed: int = 0) -> str:
    """Baseline sàn: chọn ngẫu nhiên k câu, giữ thứ tự gốc."""
    sents = _split_sentences(text)
    k = min(k, len(sents))
    idx = sorted(_random.Random(seed).sample(range(len(sents)), k))
    return " ".join(sents[i] for i in idx)
