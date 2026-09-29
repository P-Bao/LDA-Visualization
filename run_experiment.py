# -*- coding: utf-8 -*-
"""
run_experiment.py — chạy Phần 3 từ dòng lệnh, xuất kết quả ra results/ (JSON + CSV)
để đưa vào báo cáo.

Ví dụ:
    python run_experiment.py --source vietnews --limit 200 --topics 5 --top-k 3
    python run_experiment.py --source sample
"""
import argparse
import csv
import json
import os

from core.dataset_loader import load_dataset_by_source
from core.experiment import run_experiment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["sample", "vietnews"], default="sample")
    ap.add_argument("--limit", type=int, default=100)
    ap.add_argument("--split", default="test")
    ap.add_argument("--topics", type=int, default=5)
    ap.add_argument("--top-k", type=int, default=3)
    args = ap.parse_args()

    data = load_dataset_by_source(args.source, limit=args.limit, split=args.split)
    print(f"Đã nạp {len(data)} văn bản từ nguồn '{args.source}'")

    exp = run_experiment(
        data, num_topics=args.topics, top_k=args.top_k,
        progress=lambda n, t: print(f"  [{n}/{t}]", end="\r"),
    )
    print(f"\nXử lý được {exp['num_docs']} văn bản, bỏ qua {len(exp['skipped'])}.")
    print(f"Topic coherence (u_mass): {exp['coherence']:.4f}\n")
    print(f"{'Phương pháp':<10} {'R1-F1':>8} {'R2-F1':>8} {'RL-F1':>8}")
    for m in ("lda", "lead", "random"):
        a = exp["avg"][m]
        print(f"{m:<10} {a['rouge1']['f1']:>8.4f} {a['rouge2']['f1']:>8.4f} {a['rougeL']['f1']:>8.4f}")

    os.makedirs("results", exist_ok=True)
    with open("results/summary.json", "w", encoding="utf-8") as f:
        json.dump({"args": vars(args), "num_docs": exp["num_docs"],
                   "coherence": exp["coherence"], "avg": exp["avg"],
                   "skipped": exp["skipped"]}, f, ensure_ascii=False, indent=2)
    with open("results/per_doc.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "method", "rouge1_f1", "rouge2_f1", "rougeL_f1", "summary"])
        for r in exp["per_doc"]:
            for m in ("lda", "lead", "random"):
                s = r["scores"][m]
                w.writerow([r["id"], m, round(s["rouge1"]["f1"], 4),
                            round(s["rouge2"]["f1"], 4), round(s["rougeL"]["f1"], 4),
                            r["summaries"][m]])
    print("\nĐã ghi results/summary.json và results/per_doc.csv")


if __name__ == "__main__":
    main()
