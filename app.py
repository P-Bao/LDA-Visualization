# -*- coding: utf-8 -*-
"""
app.py
------
Ứng dụng web Flask gồm 3 phần theo đúng yêu cầu đề bài:

  Phần 1 (/part1)  - Mô phỏng thuật toán LDA (Gibbs sampling) từng bước trên dữ liệu nhỏ
  Phần 2 (/part2)  - Ứng dụng: tóm tắt văn bản trích xuất dựa trên LDA
  Phần 3 (/part3)  - Thử nghiệm: chạy trên một tập văn bản & đánh giá bằng ROUGE + coherence

Chạy:
    pip install -r requirements.txt
    python app.py
Rồi mở http://127.0.0.1:5000
"""

import json
import traceback

from flask import Flask, render_template, request

from core.gibbs_lda import GibbsLDA
from core.toy_data import TOY_SENTENCES
from core.nlp_utils import tokenize_and_clean
from core.lda_pipeline import summarize_extractive
from core.experiment import run_experiment
from core.dataset_loader import load_dataset_by_source

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
