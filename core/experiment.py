# -*- coding: utf-8 -*-
"""
experiment.py
-------------
Quy trình thử nghiệm PHẦN 3, dùng chung cho web (app.py) và dòng lệnh
(run_experiment.py):

  1. Với mỗi văn bản: sinh tóm tắt bằng LDA (Phần 2), lead-k, random-k.
  2. Chấm ROUGE-1/2/L so với tóm tắt tham chiếu (cột `abstract` của Vietnews).
  3. Huấn luyện LDA cấp-tập-văn-bản và tính topic coherence (u_mass).
"""

from core.lda_pipeline import (
    summarize_extractive, train_corpus_level_lda, compute_coherence,
)
from core.evaluation import (
    evaluate_document, average_scores, lead_k_summary, random_k_summary,
)


def run_experiment(dataset: list, num_topics: int = 5, top_k: int = 3,
                   corpus_topics: int = None, progress=None) -> dict:
    per_doc, skipped = [], []
    total = len(dataset)

    for n, d in enumerate(dataset, 1):
        try:
            gen = summarize_extractive(d["content"], num_topics=num_topics, top_k=top_k)
        except Exception as e:  # văn bản quá ngắn / lỗi tokenization -> bỏ qua, ghi lại
            skipped.append({"id": d["id"], "reason": str(e)})
            continue

        summaries = {
            "lda": gen["summary"],
            "lead": lead_k_summary(d["content"], top_k),
            "random": random_k_summary(d["content"], top_k, seed=n),
        }
        scores = {name: evaluate_document(d["reference_summary"], s)
                  for name, s in summaries.items()}
        per_doc.append({
            "id": d["id"], "title": d["title"], "topic_label": d.get("topic_label", ""),
            "reference_summary": d["reference_summary"],
            "summaries": summaries, "scores": scores,
        })
        if progress:
            progress(n, total)

    if not per_doc:
        raise ValueError("Không có văn bản nào xử lý được.")

    avg = {name: average_scores([r["scores"][name] for r in per_doc])
           for name in ("lda", "lead", "random")}

    documents = [d["content"] for d in dataset if d["id"] in {r["id"] for r in per_doc}]
    corpus = train_corpus_level_lda(documents, num_topics=corpus_topics or num_topics)
    coherence = compute_coherence(
        corpus["lda_model"], corpus["doc_tokens"], corpus["dictionary"], corpus["corpus"]
    )

    return {
        "per_doc": per_doc, "skipped": skipped, "avg": avg,
        "coherence": coherence, "corpus": corpus,
        "num_docs": len(per_doc),
    }
