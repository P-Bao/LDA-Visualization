# -*- coding: utf-8 -*-
"""
summarizer_pipeline.py
----------------------
Pipeline tóm tắt trích xuất bằng LDA, chạy trên Gibbs sampling TỰ CÀI ĐẶT
(core/trace_lda.py) — không dùng gensim.

Mỗi bước đều trả về dữ liệu trung gian để giao diện dựng thành "video":

  1. Tiền xử lý   : tách câu, tách từ, ghép từ ghép, bỏ stopword
  2. Ma trận đếm : câu × từ (heatmap)
  3. Huấn luyện   : vòng 1 (và 2) ghi trace từng token, các vòng sau gọn
  4. Chủ đề       : nhãn + top từ + theta từng câu
  5. Chấm điểm câu: 0.6*cos(theta_d, pi) + 0.4*xác suất token, có phạt độ dài
  6. MMR          : chọn câu đa dạng (lambda=0.7), giữ thứ tự gốc
"""

import math

from core.summarizer_preprocess import preprocess_document
from core.trace_lda import TracedGibbsLDA

# ---------------------------------------------------------------------------
# Tham số mặc định cho phần tóm tắt
# (KHÔNG sửa mặc định của lớp GibbsLDA: alpha=0.1, beta=0.01 quá thưa cho
#  một đoạn văn chỉ ~10 câu, nên truyền tham số riêng ở đây.)
# ---------------------------------------------------------------------------
DEFAULT_NUM_TOPICS = 2
MIN_NUM_TOPICS = 2
MAX_NUM_TOPICS = 4
DEFAULT_ALPHA = 0.5
DEFAULT_BETA = 0.1
DEFAULT_ITERATIONS = 30
MIN_ITERATIONS = 1
MAX_ITERATIONS = 120
DEFAULT_SEED = 42
DEFAULT_N_SENTENCES = 3
MIN_N_SENTENCES = 2
MAX_N_SENTENCES = 5
DEFAULT_MMR_LAMBDA = 0.7

# Phạt độ dài: câu quá ngắn hoặc quá dài bị nhân hệ số
SHORT_SENTENCE_TOKENS = 4
LONG_SENTENCE_TOKENS = 26
SHORT_SENTENCE_FACTOR = 0.85
LONG_SENTENCE_FACTOR = 0.92

# Ngưỡng kích thước JSON: nếu vượt thì chỉ giữ trace vòng 1
MAX_JSON_BYTES = 3 * 1024 * 1024


class PipelineError(ValueError):
    """Lỗi nghiệp vụ kèm thông báo tiếng Việt cho giao diện."""


# ---------------------------------------------------------------------------
# HÀM TOÁN HỌC
# ---------------------------------------------------------------------------

def _cosine(a, b):
    """Cosine similarity của 2 vectơ (list float)."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def _length_factor(num_tokens):
    """Hệ số phạt nhẹ cho câu quá ngắn / quá dài."""
    if num_tokens < SHORT_SENTENCE_TOKENS:
        return SHORT_SENTENCE_FACTOR
    if num_tokens > LONG_SENTENCE_TOKENS:
        return LONG_SENTENCE_FACTOR
    return 1.0


def _length_reason(num_tokens):
    """Giải thích bằng lời cho hệ số phạt (hiển thị ở cảnh 9)."""
    if num_tokens < SHORT_SENTENCE_TOKENS:
        return f"câu quá ngắn ({num_tokens} từ nội dung)"
    if num_tokens > LONG_SENTENCE_TOKENS:
        return f"câu quá dài ({num_tokens} từ nội dung)"
    return ""


# ---------------------------------------------------------------------------
# CHẤM ĐIỂM & MMR
# ---------------------------------------------------------------------------

def score_sentences(model, docs_tokens, pi, lda_index_map, sentences,
                    normalize_token_prob=False):
    """
    Chấm điểm từng câu.

        score(câu) = (0.6 * cos(theta_d, pi)      # câu có nội dung giống chủ đề
                                   đại diện của cả đoạn không?\r
                    + 0.4 * trung_bình_xác_suất_token)  # từ trong câu có dễ
                                    * he_so_do_dai       # thuộc chủ đề không?

    Tham số normalize_token_prob (mặc định False — D2):
        Khi True: chia token_prob mỗi câu cho max(token_prob) trước khi tính
        điểm, giúp phần p cùng bậc độ lớn với phần cos.
        Khi False: hành vi gốc, không đổi kết quả tóm tắt.

    Trả về danh sách dict (mỗi câu 1 phần tử) kèm từng thành phần điểm.
    Khoá bổ sung (tương thích ngược): part_cos, part_p, raw.
    """
    theta = model.theta()
    phi = model.phi_full()
    K = model.num_topics

    results = []
    for sent_idx, doc_idx in enumerate(lda_index_map):
        if doc_idx < 0:
            # Câu không còn từ nội dung: không tham gia chấm điểm/chọn câu
            results.append(
                {
                    "sentence_index": sent_idx,
                    "lda_doc": None,
                    "eligible": False,
                    "theta": [0.0] * K,
                    "cosine": 0.0,
                    "token_prob": 0.0,
                    "length_factor": 0.0,
                    "score": 0.0,
                    "num_tokens": 0,
                    "reason": "không còn từ nội dung",
                    "part_cos": 0.0,
                    "part_p": 0.0,
                    "raw": 0.0,
                }
            )
            continue

        tokens = docs_tokens[doc_idx]
        theta_d = theta[doc_idx]

        cos_sim = _cosine(theta_d, pi)

        total_prob = 0.0
        for word in tokens:
            w = model.word2id[word]
            p_word = sum(pi[k] * phi[k][w] for k in range(K))
            total_prob += p_word
        token_prob = total_prob / len(tokens) if tokens else 0.0

        results.append(
            {
                "sentence_index": sent_idx,
                "lda_doc": doc_idx,
                "eligible": True,
                "theta": [round(v, 4) for v in theta_d],
                "cosine": round(cos_sim, 4),
                "token_prob": round(token_prob, 6),
                "length_factor": _length_factor(len(tokens)),
                "score": None,   # tính sau khi chuẩn hoá (nếu cần)
                "num_tokens": len(tokens),
                "reason": _length_reason(len(tokens)),
            }
        )

    # --- Chuẩn hoá token_prob (nếu bật cờ) ----------------------------------
    eligible_results = [r for r in results if r["eligible"]]
    if normalize_token_prob and eligible_results:
        max_p = max(r["token_prob"] for r in eligible_results) or 1.0
    else:
        max_p = 1.0  # không chuẩn hoá: chia cho 1 không đổi gì

    for r in results:
        if not r["eligible"]:
            continue
        token_prob_used = r["token_prob"] / max_p
        part_cos = 0.6 * r["cosine"]
        part_p = 0.4 * token_prob_used
        raw = part_cos + part_p
        factor = r["length_factor"]
        r["score"] = round(raw * factor, 4)
        r["part_cos"] = round(part_cos, 6)
        r["part_p"] = round(part_p, 6)
        r["raw"] = round(raw, 6)

    return results



def select_sentences_mmr(scores, theta, n_sentences, mmr_lambda=DEFAULT_MMR_LAMBDA):
    """
    Chọn câu bằng MMR (Maximal Marginal Relevance):

        MMR(d) = lambda * relevance(d) - (1 - lambda) * max_sim(d, đã chọn)

    relevance = điểm câu đã chuẩn hoá min-max về [0, 1]
    max_sim   = cosine lớn nhất giữa theta_d và theta của các câu đã chọn
                (câu nào "trùng ý" nhất với phần đã chọn)

    Trả về (danh sách câu đã chọn, từng bước chọn để hiển thị ở cảnh 10).
    """
    eligible = [s for s in scores if s["eligible"]]
    if not eligible:
        return [], []

    # tra cứu nhanh theta của từng câu theo sentence_index
    theta_of = {
        s["sentence_index"]: theta[s["lda_doc"]] for s in eligible
    }

    values = [s["score"] for s in eligible]
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    relevance = {s["sentence_index"]: (s["score"] - lo) / span for s in eligible}

    n_select = max(1, min(n_sentences, len(eligible)))

    selected = []
    steps = []

    # Bước 1: câu có điểm cao nhất
    first = max(eligible, key=lambda s: s["score"])
    selected.append(first["sentence_index"])
    steps.append(
        {
            "step": 1,
            "chosen": first["sentence_index"],
            "chosen_score": first["score"],
            "candidates": [],
            "note": "Chọn câu trùng chủ đề toàn đoạn nhất làm câu trung tâm.",
        }
    )

    while len(selected) < n_select:
        best = None
        candidates = []
        for cand in eligible:
            if cand["sentence_index"] in selected:
                continue
            rel = relevance[cand["sentence_index"]]
            sim, sim_with = 0.0, None
            for sel in selected:
                s_val = _cosine(cand["theta"], theta_of[sel])
                if s_val > sim:
                    sim, sim_with = s_val, sel
            mmr = mmr_lambda * rel - (1.0 - mmr_lambda) * sim
            candidates.append(
                {
                    "sentence_index": cand["sentence_index"],
                    "mmr": round(mmr, 4),
                    "relevance": round(rel, 4),
                    "redundancy": round(sim, 4),
                    "redundant_with": sim_with,
                }
            )
            if best is None or mmr > best[0]:
                best = (mmr, cand, sim_with)

        if best is None:
            break

        mmr_val, chosen, sim_with = best
        selected.append(chosen["sentence_index"])
        candidates.sort(key=lambda c: c["mmr"], reverse=True)
        steps.append(
            {
                "step": len(steps) + 1,
                "chosen": chosen["sentence_index"],
                "chosen_score": chosen["score"],
                "mmr_value": round(mmr_val, 4),
                "candidates": candidates,
                "note": (
                    f"Cân bằng giữa độ trùng chủ đề và sự khác biệt "
                    f"(λ={mmr_lambda}); câu đã chọn gần nhất là câu "
                    f"{(sim_with + 1) if sim_with is not None else '—'}."
                ),
            }
        )

    return sorted(selected), steps


def _rejected_reasons(scores, selected, theta):
    """Giải thích vì sao các câu còn lại bị loại (cho cảnh 10)."""
    rejected = []
    selected_scores = [s for s in scores if s["sentence_index"] in selected]
    best_selected = min((s["score"] for s in selected_scores), default=0.0)

    for s in scores:
        if not s["eligible"] or s["sentence_index"] in selected:
            continue
        sim, sim_with = 0.0, None
        for sel_score in selected_scores:
            s_val = _cosine(s["theta"], theta[sel_score["lda_doc"]])
            if s_val > sim:
                sim, sim_with = s_val, sel_score["sentence_index"]
        if sim >= 0.75:
            reason = (
                f"trùng ý với câu {sim_with + 1} (cos={sim:.2f} ≥ 0.75)"
            )
        elif s["score"] <= best_selected:
            reason = f"điểm thấp hơn các câu đã chọn ({s['score']:.3f})"
        else:
            reason = (
                f"bị loại do cân bằng MMR (cos với câu {sim_with + 1} = {sim:.2f})"
            )
        rejected.append(
            {
                "sentence_index": s["sentence_index"],
                "score": s["score"],
                "similarity": round(sim, 4),
                "similar_with": sim_with,
                "reason": reason,
            }
        )
    return rejected


# ---------------------------------------------------------------------------
# HÀM CHÍNH
# ---------------------------------------------------------------------------

def summarize_document(
    text,
    num_topics=DEFAULT_NUM_TOPICS,
    iterations=DEFAULT_ITERATIONS,
    alpha=DEFAULT_ALPHA,
    beta=DEFAULT_BETA,
    seed=DEFAULT_SEED,
    n_sentences=DEFAULT_N_SENTENCES,
    mmr_lambda=DEFAULT_MMR_LAMBDA,
    trace_iterations=(1,),
    dev_checks=False,
    normalize_token_prob=False,
):
    """
    Chạy toàn bộ pipeline và trả về một dict JSON-serializable chứa dữ liệu
    cho mọi cảnh của giao diện "video".
    """
    # --- 1. Tiền xử lý ------------------------------------------------
    prep = preprocess_document(text)
    docs_tokens = prep["docs_tokens"]
    lda_index_map = prep["lda_index_map"]
    sentences = prep["sentences"]

    # --- 2. Kiểm tra & chuẩn hoá tham số -----------------------------
    K = int(num_topics)
    if K < MIN_NUM_TOPICS:
        raise PipelineError(f"Số chủ đề K phải ít nhất là {MIN_NUM_TOPICS}.")
    if K > MAX_NUM_TOPICS:
        raise PipelineError(f"Số chủ đề K không vượt quá {MAX_NUM_TOPICS}.")

    vocab_size = len(set(w for doc in docs_tokens for w in doc))
    if K > vocab_size:
        raise PipelineError(
            f"Số chủ đề K={K} lớn hơn số từ vựng ({vocab_size} từ). "
            f"Vui lòng giảm K hoặc dùng đoạn văn dài hơn."
        )

    iterations = max(MIN_ITERATIONS, min(int(iterations), MAX_ITERATIONS))
    n_sentences = max(
        MIN_N_SENTENCES, min(int(n_sentences), MAX_N_SENTENCES, len(docs_tokens))
    )

    # --- 3. Huấn luyện: vòng 1 (và 2) có trace, các vòng sau chạy nhanh --
    model = TracedGibbsLDA(
        docs_tokens, num_topics=K, alpha=alpha, beta=beta, seed=int(seed)
    )

    history = [model.snapshot()]
    traces = {}

    wanted = sorted({int(i) for i in trace_iterations if 1 <= int(i) <= iterations})
    for it in range(1, iterations + 1):
        if it in wanted:
            traces[it] = model.sweep_with_trace()
        else:
            model.gibbs_sweep()
        history.append(model.snapshot())
        if dev_checks:
            model.assert_counts_consistent()

    if dev_checks:
        model.assert_counts_consistent()
        model.assert_z_consistent()

    # --- 4. Kết quả chủ đề -------------------------------------------
    theta = model.theta()
    phi = model.phi_full()
    labels = model.topic_labels(topn=3)
    topic_words = [
        [
            (w, round(p, 5))
            for w, p in topic
        ]
        for topic in model.phi(topn=8)
    ]

    # Phân bố chủ đề toàn đoạn pi_k: trung bình theta có trọng số theo n_d
    total_tokens = sum(model.n_d) or 1
    pi = [
        sum(model.n_d[d] * theta[d][k] for d in range(model.D)) / total_tokens
        for k in range(K)
    ]

    # --- 5. Chấm điểm câu ---------------------------------------------
    scores = score_sentences(model, docs_tokens, pi, lda_index_map, sentences,
                             normalize_token_prob=normalize_token_prob)

    # --- 6. Chọn câu bằng MMR ----------------------------------------
    selected, mmr_steps = select_sentences_mmr(
        scores, theta, n_sentences, mmr_lambda=mmr_lambda
    )
    rejected = _rejected_reasons(scores, selected, theta)

    # --- 7. Tóm tắt theo THỨ TỰ GỐC ---------------------------------
    summary_sentences = [
        {"sentence_index": i, "text": sentences[i]} for i in selected
    ]
    summary_text = " ".join(s["text"] for s in summary_sentences)

    num_words_original = prep["stats"]["num_raw_words"]
    num_words_summary = len(summary_text.split())
    compression = (
        round(num_words_original / num_words_summary, 2)
        if num_words_summary
        else 0.0
    )

    # --- 8. Gói dữ liệu cho từng cảnh giao diện ----------------------
    payload = {
        "params": {
            "num_topics": K,
            "iterations": iterations,
            "alpha": alpha,
            "beta": beta,
            "seed": int(seed),
            "n_sentences": n_sentences,
            "mmr_lambda": mmr_lambda,
            "trace_iterations": wanted,
            "normalize_token_prob": normalize_token_prob,
        },
        "input": {
            "text": (text or "").strip(),
            "num_raw_words": num_words_original,
        },
        "stats": prep["stats"],
        "sentences": [
            {
                "index": i,
                "text": sentences[i],
                "lda_doc": lda_index_map[i],
                "is_empty": lda_index_map[i] < 0,
                "num_tokens": sum(
                    1
                    for t in prep["sentence_tokens"][i]
                    if t["type"] in ("compound", "word")
                ),
            }
            for i in range(len(sentences))
        ],
        "sentence_tokens": prep["sentence_tokens"],
        "heatmap": {
            "vocab": prep["vocab"],
            "matrix": prep["matrix"],
            "max_count": prep["max_count"],
        },
        "vocab": model.vocab,
        "initial": {
            "assignments": history[0]["assignments"],
            "theta": history[0]["theta"],
            "log_likelihood": history[0]["log_likelihood"],
        },
        "history": history,
        "traces": traces,
        "topics": {
            "labels": labels,
            "top_words": topic_words,
            "phi": [[round(v, 6) for v in row] for row in phi],
            "phi_top": [[prob for _, prob in topic] for topic in topic_words],
            "pi": [round(v, 5) for v in pi],
        },
        "n_d": list(model.n_d),
        "scores": scores,
        "mmr": {
            "lambda": mmr_lambda,
            "selected": selected,
            "steps": mmr_steps,
            "rejected": rejected,
        },
        "summary": {
            "sentences": summary_sentences,
            "text": summary_text,
            "num_words_original": num_words_original,
            "num_words_summary": num_words_summary,
            "num_sentences_original": len(sentences),
            "num_sentences_summary": len(selected),
            "compression_ratio": compression,
        },
    }

    # Giữ lại số đếm khởi tạo (n_dk, n_kw, n_k) cho cảnh 5
    payload["initial_counts"] = _initial_counts_from(prep, K, int(seed), alpha, beta)

    # Nếu JSON quá lớn: chỉ giữ trace vòng 1
    _trim_traces_if_needed(payload)

    return payload


def _initial_counts_from(prep, K, seed, alpha, beta):
    """
    Chạy lại mô hình ở trạng thái khởi tạo (chỉ khởi tạo, chưa sweep) để lấy
    z, n_dk, n_kw, n_k ban đầu cho cảnh 5 — việc này tất định với seed nên
    không ảnh hưởng kết quả mô hình chính.
    """
    model = TracedGibbsLDA(
        prep["docs_tokens"], num_topics=K, alpha=alpha, beta=beta, seed=seed
    )
    word_totals = [sum(model.n_kw[k][w] for k in range(K)) for w in range(model.V)]
    sorted_words = sorted(range(model.V), key=lambda w: word_totals[w], reverse=True)
    top_kw_table = [
        {
            "word": model.vocab[w],
            "counts": [model.n_kw[k][w] for k in range(K)],
            "total": word_totals[w],
        }
        for w in sorted_words[:20]
    ]

    return {
        "assignments": [list(z_doc) for z_doc in model.z],
        "n_dk": [list(row) for row in model.n_dk],
        "n_kw": [
            [
                {"word": model.vocab[w], "count": model.n_kw[k][w]}
                for w in range(model.V)
                if model.n_kw[k][w] > 0
            ]
            for k in range(K)
        ],
        "top_kw_table": top_kw_table,
        "n_k": list(model.n_k),
        "n_d": list(model.n_d),
        "vocab": list(model.vocab),
    }


def _trim_traces_if_needed(payload):
    """Nếu payload quá lớn thì bỏ trace ngoài vòng 1 (giữ nguyên cảnh 6)."""
    import json

    size = len(json.dumps(payload, ensure_ascii=False))
    if size <= MAX_JSON_BYTES:
        payload["meta"] = {"json_bytes": size, "traces_kept": sorted(payload["traces"])}
        return

    for key in sorted(payload["traces"], reverse=True):
        if key == 1:
            break
        del payload["traces"][key]

    size = len(json.dumps(payload, ensure_ascii=False))
    payload["meta"] = {
        "json_bytes": size,
        "traces_kept": sorted(payload["traces"]),
        "trimmed": True,
    }
