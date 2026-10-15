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
  5. Chấm điểm câu: Xác suất sinh hậu nghiệm trung bình (Griffiths & Steyvers 2004)
  6. MMR          : JSD-MMR trên đơn hình Dirichlet (lambda=0.7), giữ thứ tự gốc
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
MAX_NUM_TOPICS = 15
DEFAULT_ALPHA = 0.5
DEFAULT_BETA = 0.1
DEFAULT_ITERATIONS = 30
MIN_ITERATIONS = 1
MAX_ITERATIONS = 5000
DEFAULT_SEED = 42
DEFAULT_N_SENTENCES = 3
MIN_N_SENTENCES = 2
MAX_N_SENTENCES = 15
DEFAULT_MMR_LAMBDA = 0.7

# Phương án A: Giữ đầy đủ toàn bộ snapshot cho tới 5000 vòng lặp
MAX_JSON_BYTES = 50 * 1024 * 1024


class PipelineError(ValueError):
    """Lỗi nghiệp vụ kèm thông báo tiếng Việt cho giao diện."""


# ---------------------------------------------------------------------------
# HÀM LÝ THUYẾT THÔNG TIN (KL & Jensen-Shannon trên đơn hình Dirichlet)
# ---------------------------------------------------------------------------

def _kl_divergence(p, q):
    """
    Phân kỳ Kullback-Leibler D_KL(P || Q) = sum_k P_k * ln(P_k / Q_k)
    (Blei, Ng & Jordan, JMLR 2003, Eq. 5).
    """
    kl = 0.0
    for pk, qk in zip(p, q):
        if pk > 1e-12:
            kl += pk * math.log(pk / max(qk, 1e-12))
    return max(0.0, kl)


def _js_divergence(p, q):
    """
    Phân kỳ Jensen-Shannon chuẩn hoá về [0, 1] trên đơn hình Dirichlet:
    D_JS(P || Q) = [0.5 * D_KL(P || M) + 0.5 * D_KL(Q || M)] / ln(2), với M = 0.5*(P + Q)
    (Lin, 1991; Louis & Nenkova, EMNLP 2009; Hennig, RANLP 2009).
    """
    m = [0.5 * (pk + qk) for pk, qk in zip(p, q)]
    js = 0.5 * _kl_divergence(p, m) + 0.5 * _kl_divergence(q, m)
    norm_js = js / math.log(2.0)
    return min(1.0, max(0.0, norm_js))


def _js_similarity(p, q):
    """
    Độ tương đồng chủ đề trên đơn hình Dirichlet: Sim_JS(P, Q) = 1 - D_JS(P || Q) thuộc [0, 1].
    """
    return 1.0 - _js_divergence(p, q)


# ---------------------------------------------------------------------------
# CHẤM ĐIỂM (CẢNH 9) & MMR (CẢNH 10)
# ---------------------------------------------------------------------------

def score_sentences(model, docs_tokens, pi, lda_index_map, sentences):
    """
    Chấm điểm từng câu dựa trên Xác suất Sinh Hậu nghiệm Trung bình
    (Griffiths & Steyvers, PNAS 2004 - Eq. 1, 6, 7 & Haghighi & Vanderwende, NAACL 2009):

        RawScore(d) = (1 / n_d) * sum_{w in d} sum_{k=1..K} [ pi_k * theta_{d,k} * phi_{k,w} ]
                    = sum_{k=1..K} topic_parts[k]

    Score(d) = RawScore(d) / max_{d'} RawScore(d') thuộc [0, 1].
    """
    theta = model.theta()
    phi = model.phi_full()
    K = model.num_topics

    results = []
    for sent_idx, doc_idx in enumerate(lda_index_map):
        if doc_idx < 0:
            results.append(
                {
                    "sentence_index": sent_idx,
                    "lda_doc": None,
                    "eligible": False,
                    "theta": [0.0] * K,
                    "mean_phi": [0.0] * K,
                    "topic_parts": [0.0] * K,
                    "topic_parts_norm": [0.0] * K,
                    "raw_score": 0.0,
                    "score": 0.0,
                    "num_tokens": 0,
                    "reason": "không còn từ nội dung",
                }
            )
            continue

        tokens = docs_tokens[doc_idx]
        theta_d = theta[doc_idx]
        n_tok = len(tokens)

        mean_phi = []
        topic_parts = []
        for k in range(K):
            m_phi_k = (
                sum(phi[k][model.word2id[word]] for word in tokens) / n_tok
                if n_tok
                else 0.0
            )
            mean_phi.append(m_phi_k)
            topic_parts.append(pi[k] * theta_d[k] * m_phi_k)

        raw_score = sum(topic_parts)

        results.append(
            {
                "sentence_index": sent_idx,
                "lda_doc": doc_idx,
                "eligible": True,
                "theta": [round(v, 4) for v in theta_d],
                "mean_phi": [round(v, 6) for v in mean_phi],
                "topic_parts": [round(v, 6) for v in topic_parts],
                "topic_parts_norm": [0.0] * K,
                "raw_score": round(raw_score, 6),
                "score": 0.0,
                "num_tokens": n_tok,
                "reason": "",
            }
        )

    eligible_results = [r for r in results if r["eligible"]]
    max_raw = max((r["raw_score"] for r in eligible_results), default=0.0) or 1.0

    for r in results:
        if not r["eligible"]:
            continue
        r["topic_parts_norm"] = [round(p / max_raw, 4) for p in r["topic_parts"]]
        r["score"] = round(r["raw_score"] / max_raw, 4)

    return results


def select_sentences_mmr(scores, theta, n_sentences, mmr_lambda=DEFAULT_MMR_LAMBDA):
    """
    Chọn câu bằng JSD-MMR trên đơn hình Dirichlet
    (Blei et al., 2003, Eq. 5; Louis & Nenkova, EMNLP 2009; Hennig, RANLP 2009;
     Carbonell & Goldstein, SIGIR 1998):

        MMR_JS(d) = lambda * Score(d) - (1 - lambda) * max_{j in S} Sim_JS(theta_d, theta_j)
        với Sim_JS(P, Q) = 1 - D_JS(P || Q) thuộc [0, 1].
    """
    eligible = [s for s in scores if s["eligible"]]
    if not eligible:
        return [], []

    theta_of = {
        s["sentence_index"]: theta[s["lda_doc"]] for s in eligible
    }

    n_select = max(1, min(n_sentences, len(eligible)))

    selected = []
    steps = []

    # Bước 1: câu có xác suất sinh hậu nghiệm Score(d) cao nhất
    first = max(eligible, key=lambda s: s["score"])
    selected.append(first["sentence_index"])
    steps.append(
        {
            "step": 1,
            "chosen": first["sentence_index"],
            "chosen_score": first["score"],
            "candidates": [],
            "note": "Bước 1: Chọn câu có xác suất sinh hậu nghiệm Score(d) cao nhất làm hạt nhân chủ đề.",
        }
    )

    while len(selected) < n_select:
        best = None
        candidates = []
        for cand in eligible:
            if cand["sentence_index"] in selected:
                continue
            rel = cand["score"]
            cand_theta = theta_of[cand["sentence_index"]]
            sim, min_jsd, sim_with = 0.0, 1.0, None
            for sel in selected:
                s_val = _js_similarity(cand_theta, theta_of[sel])
                if s_val > sim:
                    sim = s_val
                    min_jsd = 1.0 - s_val
                    sim_with = sel
            mmr = mmr_lambda * rel - (1.0 - mmr_lambda) * sim
            candidates.append(
                {
                    "sentence_index": cand["sentence_index"],
                    "mmr": round(mmr, 4),
                    "relevance": round(rel, 4),
                    "js_divergence": round(min_jsd, 4),
                    "redundancy": round(sim, 4),
                    "redundant_with": sim_with,
                }
            )
            if best is None or mmr > best[0]:
                best = (mmr, cand, sim_with, min_jsd)

        if best is None:
            break

        mmr_val, chosen, sim_with, min_jsd = best
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
                    f"Cực đại hoá JSD-MMR (λ={mmr_lambda}); câu đã chọn gần chủ đề nhất là câu "
                    f"{(sim_with + 1) if sim_with is not None else '—'} "
                    f"(D_JS={min_jsd:.3f}, Sim_JS={1.0 - min_jsd:.3f})."
                ),
            }
        )

    return sorted(selected), steps


def _rejected_reasons(scores, selected, theta):
    """Giải thích vì sao các câu còn lại bị loại dựa trên D_JS và Score(d) (cho cảnh 10)."""
    rejected = []
    selected_scores = [s for s in scores if s["sentence_index"] in selected]
    min_selected_score = min((s["score"] for s in selected_scores), default=0.0)

    for s in scores:
        if not s["eligible"] or s["sentence_index"] in selected:
            continue
        s_theta = theta[s["lda_doc"]]
        sim, sim_with = 0.0, None
        for sel_score in selected_scores:
            s_val = _js_similarity(s_theta, theta[sel_score["lda_doc"]])
            if s_val > sim:
                sim, sim_with = s_val, sel_score["sentence_index"]
        js_div = 1.0 - sim
        if sim >= 0.75:
            reason = (
                f"phân phối chủ đề trùng lặp với câu {sim_with + 1} "
                f"(Sim_JS={sim:.2f} ≥ 0.75, D_JS={js_div:.2f})"
            )
        elif s["score"] <= min_selected_score:
            reason = f"xác suất sinh hậu nghiệm thấp hơn các câu đã chọn (Score={s['score']:.3f})"
        else:
            reason = (
                f"bị loại khi cân bằng JSD-MMR (Sim_JS với câu {sim_with + 1} = {sim:.2f})"
            )
        rejected.append(
            {
                "sentence_index": s["sentence_index"],
                "score": s["score"],
                "js_divergence": round(js_div, 4),
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
    scores = score_sentences(model, docs_tokens, pi, lda_index_map, sentences)

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
