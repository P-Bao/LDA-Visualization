# -*- coding: utf-8 -*-
"""
Tải danh sách stopword tiếng Việt công khai và gộp vào data/stopwords_vi.txt.

    python scripts/download_stopwords.py

Nguồn mặc định: github.com/stopwords/vietnamese-stopwords
(cần internet; nếu URL đổi, tải file .txt thủ công rồi dùng --file).
"""
import argparse
import os
import urllib.request

URL = "https://raw.githubusercontent.com/stopwords/vietnamese-stopwords/master/vietnamese-stopwords.txt"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "data", "stopwords_vi.txt")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=URL)
    ap.add_argument("--file", help="Dùng file txt cục bộ thay vì tải từ URL")
    args = ap.parse_args()

    if args.file:
        raw = open(args.file, encoding="utf-8").read()
    else:
        raw = urllib.request.urlopen(args.url, timeout=30).read().decode("utf-8")

    new = {w.strip().lower() for w in raw.splitlines() if w.strip()}
    old = set()
    if os.path.exists(OUT):
        old = {w.strip().lower() for w in open(OUT, encoding="utf-8") if w.strip()}

    merged = sorted(old | new)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(merged) + "\n")
    print(f"Đã ghi {len(merged)} stopword vào {OUT} (mới thêm {len(merged) - len(old)}).")


if __name__ == "__main__":
    main()
