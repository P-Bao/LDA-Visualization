# -*- coding: utf-8 -*-
"""
app.py
------
Ứng dụng web Flask gồm 3 phần theo đúng yêu cầu đề bài:

  Phần 1 (/part1)  - Mô phỏng thuật toán LDA (Gibbs sampling) từng bước trên dữ liệu nhỏ
  Phần 1' (/summarize) - Tóm tắt văn bản trích xuất, trình bày như "video" từng bước
  Phần 2 (/part2)  - Ứng dụng: tóm tắt văn bản trích xuất dựa trên LDA
  Phần 3 (/part3)  - Thử nghiệm: chạy trên một tập văn bản & đánh giá bằng ROUGE + coherence

Chạy:
    pip install -r requirements.txt
    python app.py
Rồi mở http://127.0.0.1:5000
"""

import json
import traceback

from flask import Flask, jsonify, render_template, request

from core.gibbs_lda import GibbsLDA
from core.toy_data import TOY_SENTENCES
from core.nlp_utils import tokenize_and_clean
from core.lda_pipeline import summarize_extractive
from core.experiment import run_experiment
from core.dataset_loader import load_dataset_by_source
from core.sample_text import SAMPLE_TEXT_SUMMARIZE
from core.summarizer_pipeline import (
    DEFAULT_ALPHA,
    DEFAULT_BETA,
    DEFAULT_ITERATIONS,
    DEFAULT_N_SENTENCES,
    DEFAULT_NUM_TOPICS,
    DEFAULT_SEED,
    MAX_ITERATIONS,
    MAX_N_SENTENCES,
    MAX_NUM_TOPICS,
    MIN_ITERATIONS,
    MIN_N_SENTENCES,
    MIN_NUM_TOPICS,
    summarize_document,
)

app = Flask(__name__)

SAMPLE_TEXT_PART2 = (
    "Trí tuệ nhân tạo đang thay đổi cách con người làm việc và học tập. "
    "Nhiều doanh nghiệp Việt Nam đã ứng dụng trí tuệ nhân tạo vào sản xuất để tăng năng suất. "
    "Trong lĩnh vực y tế, các bác sĩ sử dụng công nghệ để chẩn đoán bệnh sớm và chính xác hơn. "
    "Bên cạnh đó, giáo dục cũng được hưởng lợi khi học sinh có thể học cá nhân hoá theo tốc độ riêng. "
    "Tuy nhiên, sự phát triển của công nghệ cũng đặt ra nhiều thách thức về việc làm. "
    "Người lao động ở một số ngành nghề truyền thống có nguy cơ bị thay thế bởi tự động hoá. "
    "Chính phủ và các trường đại học cần phối hợp để đào tạo lại kỹ năng cho người lao động. "
    "Nhìn chung, công nghệ mang lại cả cơ hội lẫn thách thức cho xã hội hiện đại."
)


@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# PHẦN 1 — Mô phỏng thuật toán từng bước
# ---------------------------------------------------------------------------
@app.route("/part1")
def part1():
    num_topics = int(request.args.get("num_topics", 2))
    num_iterations = int(request.args.get("num_iterations", 20))

    toy_tokens = [tokenize_and_clean(s) for s in TOY_SENTENCES]
    model = GibbsLDA(toy_tokens, num_topics=num_topics, alpha=0.1, beta=0.01, seed=42)
    history = model.run_and_record(num_iterations=num_iterations)

    return render_template(
        "part1.html",
        sentences=TOY_SENTENCES,
        tokens=toy_tokens,
        num_topics=num_topics,
        num_iterations=num_iterations,
        history_json=json.dumps(history, ensure_ascii=False),
    )


# ---------------------------------------------------------------------------
# PHẦN 1' — TÓM TẮT DẠNG "VIDEO": từ đoạn văn tới bản tóm tắt, từng bước
# (Dùng chính Gibbs sampling tự cài đặt ở core/trace_lda.py — thuần Python.)
# ---------------------------------------------------------------------------
@app.route("/summarize", methods=["GET"])
def summarize():
    return render_template(
        "summarize.html",
        sample_text=SAMPLE_TEXT_SUMMARIZE,
        defaults={
            "num_topics": DEFAULT_NUM_TOPICS,
            "iterations": DEFAULT_ITERATIONS,
            "alpha": DEFAULT_ALPHA,
            "beta": DEFAULT_BETA,
            "seed": DEFAULT_SEED,
            "n_sentences": DEFAULT_N_SENTENCES,
        },
        bounds={
            "min_topics": MIN_NUM_TOPICS,
            "max_topics": MAX_NUM_TOPICS,
            "min_iterations": MIN_ITERATIONS,
            "max_iterations": MAX_ITERATIONS,
            "min_sentences": MIN_N_SENTENCES,
            "max_sentences": MAX_N_SENTENCES,
        },
    )


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    """
    Nhận {text, K, iterations, alpha, beta, seed, n_sentences} và trả về
    JSON chứa dữ liệu trung gian của MỌI cảnh (kể cả trace vòng 1) để giao
    diện phát lại thành video.
    """
    payload = request.get_json(silent=True) or request.form

    text = (payload.get("text") or "").strip()

    def _num(key, default):
        try:
            return int(payload.get(key, default))
        except (TypeError, ValueError):
            return default

    def _flt(key, default):
        try:
            return float(payload.get(key, default))
        except (TypeError, ValueError):
            return default

    try:
        result = summarize_document(
            text,
            num_topics=_num("K", DEFAULT_NUM_TOPICS),
            iterations=_num("iterations", DEFAULT_ITERATIONS),
            alpha=_flt("alpha", DEFAULT_ALPHA),
            beta=_flt("beta", DEFAULT_BETA),
            seed=_num("seed", DEFAULT_SEED),
            n_sentences=_num("n_sentences", DEFAULT_N_SENTENCES),
        )
    except ValueError as e:
        # Lỗi nghiệp vụ có thông báo tiếng Việt sẵn (quá ngắn / quá dài /
        # K vượt từ vựng / thiếu văn bản) -> trả về 400 cho giao diện hiển thị.
        return jsonify({"error": str(e)}), 400
    except Exception as e:  # noqa: BLE001 - lỗi ngoài dự kiến
        traceback.print_exc()
        return jsonify({"error": f"Lỗi xử lý: {e}"}), 500

    return jsonify(result)


# ---------------------------------------------------------------------------
# PHẦN 2 — Ứng dụng tóm tắt văn bản trích xuất
# ---------------------------------------------------------------------------
@app.route("/part2", methods=["GET"])
def part2():
    return render_template("part2.html", sample_text=SAMPLE_TEXT_PART2)


@app.route("/part2/analyze", methods=["POST"])
def part2_analyze():
    text = request.form.get("text", "").strip()
    num_topics = int(request.form.get("num_topics", 4))
    top_k = int(request.form.get("top_k", 3))

    if not text:
        return render_template("part2.html", sample_text=SAMPLE_TEXT_PART2, error="Vui lòng nhập văn bản.")

    try:
        result = summarize_extractive(text, num_topics=num_topics, top_k=top_k)
    except Exception as e:
        traceback.print_exc()
        return render_template("part2.html", sample_text=SAMPLE_TEXT_PART2, error=f"Lỗi xử lý: {e}")

    topic_bar_data = [
        {
            "topic": f"Chủ đề {int(tid) + 1}",
            "words": [w for w, _ in words],
            "weights": [round(float(w), 4) for _, w in words],
        }
        for tid, words in result["topic_words"].items()
    ]
    doc_dist_data = {
        "labels": [f"Chủ đề {i + 1}" for i in range(result["num_topics"])],
        "values": [round(v, 4) for v in result["doc_dist"]],
    }
    heatmap_data = {
        "sentences": [
            (d["sentence"][:60] + "…") if len(d["sentence"]) > 60 else d["sentence"]
            for d in result["sentence_detail"]
        ],
        "z": [d["topic_distribution"] for d in result["sentence_detail"]],
        "topics": [f"Chủ đề {i + 1}" for i in range(result["num_topics"])],
        "selected": [d["selected"] for d in result["sentence_detail"]],
    }

    return render_template(
        "part2_result.html",
        summary=result["summary"],
        original_text=text,
        topic_bar_json=json.dumps(topic_bar_data, ensure_ascii=False),
        doc_dist_json=json.dumps(doc_dist_data, ensure_ascii=False),
        heatmap_json=json.dumps(heatmap_data, ensure_ascii=False),
    )


# ---------------------------------------------------------------------------
# PHẦN 3 — Thử nghiệm trên một tập văn bản & đánh giá
# ---------------------------------------------------------------------------
@app.route("/part3", methods=["GET"])
def part3():
    return render_template("part3.html")


@app.route("/part3/run", methods=["POST"])
def part3_run():
    source = request.form.get("source", "sample")
    num_topics = int(request.form.get("num_topics", 5))
    top_k = int(request.form.get("top_k", 3))
    limit = int(request.form.get("limit", 50))

    try:
        dataset = load_dataset_by_source(source, limit=limit)
        exp = run_experiment(dataset, num_topics=num_topics, top_k=top_k)
    except Exception as e:
        traceback.print_exc()
        return render_template("part3.html", error=f"Lỗi xử lý: {e}")

    per_doc, corpus = exp["per_doc"], exp["corpus"]
    methods = [("lda", "LDA (Phần 2)"), ("lead", "Lead-k"), ("random", "Random-k")]

    avg_chart = {
        "methods": [label for _, label in methods],
        "rouge1": [exp["avg"][m]["rouge1"]["f1"] for m, _ in methods],
        "rouge2": [exp["avg"][m]["rouge2"]["f1"] for m, _ in methods],
        "rougeL": [exp["avg"][m]["rougeL"]["f1"] for m, _ in methods],
    }
    topic_bar_data = [
        {"topic": f"Chủ đề {int(tid) + 1}",
         "words": [w for w, _ in words],
         "weights": [round(float(x), 4) for _, x in words]}
        for tid, words in corpus["topic_words"].items()
    ]
    shown = per_doc[:30]  # heatmap chỉ vẽ tối đa 30 văn bản cho dễ đọc
    heatmap = {
        "labels": [r["id"][:10] for r in shown],
        "z": corpus["doc_topic_matrix"][:len(shown)],
        "topics": [f"Chủ đề {i + 1}" for i in range(corpus["num_topics"])],
    }

    return render_template(
        "part3_result.html",
        exp=exp, methods=methods, source=source, top_k=top_k,
        rows=per_doc[:20], num_topics=corpus["num_topics"],
        coherence=round(exp["coherence"], 4),
        avg_chart_json=json.dumps(avg_chart, ensure_ascii=False),
        topic_bar_json=json.dumps(topic_bar_data, ensure_ascii=False),
        heatmap_json=json.dumps(heatmap, ensure_ascii=False),
    )


if __name__ == "__main__":
    app.run(debug=True)
