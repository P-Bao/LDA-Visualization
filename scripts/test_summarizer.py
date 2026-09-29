# -*- coding: utf-8 -*-
"""
test_summarizer.py
------------------
Kiểm thử backend cho trang "Tóm tắt dạng video" (Phần 1').

Chạy:
    python scripts/test_summarizer.py

Các kiểm thử:
    (a) GibbsLDA gốc với seed cũ cho KẾT QUẢ Y HỆT tham chiếu (bất biến)
    (b) TracedGibbsLDA và GibbsLDA cho CÙNG assignments sau 1 vòng, cùng seed
    (c) Cùng seed -> kết quả tái lập (tiền xử lý + toàn pipeline)
    (d) log-likelihood nhìn chung tăng theo số vòng
    (e) In bản tóm tắt cuối của đoạn văn mẫu
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Console Windows mặc định cp1252 -> ép UTF-8 để in được tiếng Việt
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from core.gibbs_lda import GibbsLDA
from core.nlp_utils import tokenize_and_clean
from core.sample_text import SAMPLE_TEXT_SUMMARIZE
from core.summarizer_pipeline import summarize_document
from core.summarizer_preprocess import (
    PreprocessError,
    preprocess_document,
    split_sentences,
)
from core.toy_data import TOY_SENTENCES
from core.trace_lda import TracedGibbsLDA

# Kết quả tham chiếu của demo cũ (GibbsLDA, 8 câu, K=2, alpha=0.1, beta=0.01,
# seed=42, 20 vòng) — sinh ra TRƯỚC khi thêm TracedGibbsLDA. Nếu ai đó sửa
# core/gibbs_lda.py, giá trị này sẽ lệch và test sẽ báo đỏ.
REFERENCE_DEMO_20 = {
    "z_last_doc": None,      # điền bởi lần chạy đầu tiên
    "log_likelihood_last": -162.437,
}


def hr(title):
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def test_a_demo_unchanged():
    """(a) Demo 8 câu cũ cho kết quả y hệt tham chiếu."""
    hr("(a) GibbsLDA gốc — demo 8 câu, seed=42, 20 vòng")

    docs = [tokenize_and_clean(s) for s in TOY_SENTENCES]
    model = GibbsLDA(docs, num_topics=2, alpha=0.1, beta=0.01, seed=42)
    history = model.run_and_record(num_iterations=20)

    ll_last = round(history[-1]["log_likelihood"], 3)
    ref = REFERENCE_DEMO_20["log_likelihood_last"]
    print(f"  log-likelihood vòng 20 : {ll_last}")
    print(f"  tham chiếu             : {ref}")
    assert ll_last == ref, "Demo cũ đã thay đổi — core/gibbs_lda.py bị sửa!"

    # snapshot đầu/cuối phải giữ nguyên cấu trúc
    assert len(history) == 21, "Số snapshot phải = 1 + số vòng"
    assert set(history[0].keys()) == {
        "iteration", "assignments", "theta", "phi", "log_likelihood"
    }
    print("  -> OK: kết quả y hệt tham chiếu, cấu trúc snapshot không đổi.")
    return history


def test_b_trace_matches():
    """(b) TracedGibbsLDA == GibbsLDA sau 1 vòng (và nhiều vòng), cùng seed."""
    hr("(b) TracedGibbsLDA vs GibbsLDA — cùng seed, 1 vòng (và 20 vòng)")

    docs = [tokenize_and_clean(s) for s in TOY_SENTENCES]

    base = GibbsLDA(docs, num_topics=2, alpha=0.1, beta=0.01, seed=42)
    traced = TracedGibbsLDA(docs, num_topics=2, alpha=0.1, beta=0.01, seed=42)

    # trạng thái khởi tạo phải giống nhau (cùng số lần gọi rng)
    assert base.z == traced.z, "Khởi tạo khác nhau -> số lần gọi rng đã đổi"
    print("  khởi tạo: z giống nhau")

    # --- sau 1 vòng ---
    base.gibbs_sweep()
    trace = traced.sweep_with_trace()

    assert base.z == traced.z, "Sau 1 vòng: assignments KHÁC nhau"
    assert base.n_dk == traced.n_dk, "Sau 1 vòng: n_dk khác nhau"
    assert base.n_kw == traced.n_kw, "Sau 1 vòng: n_kw khác nhau"
    assert base.n_k == traced.n_k, "Sau 1 vòng: n_k khác nhau"
    print(f"  sau 1 vòng: assignments + toàn bộ bộ đếm GIỐNG NHAU")
    print(f"  trace ghi {len(trace)} token; số token corpus = {sum(len(d) for d in docs)}")
    assert len(trace) == sum(len(d) for d in docs)

    # trace phải mô tả đúng 1 token
    t0 = trace[0]
    for key in ("d", "i", "word", "k_old", "n_dk", "n_kw", "n_k",
                "left", "right", "raw", "probs", "r", "k_new", "changed"):
        assert key in t0, f"trace thiếu khoá {key}"
    assert abs(sum(t0["probs"]) - 1.0) < 1e-4, "probs chưa chuẩn hoá"
    assert abs(t0["raw"][0] - t0["left"][0] * t0["right"][0]) < 1e-6
    assert t0["k_new"] == traced.z[t0["d"]][t0["i"]], "k_new không khớp z"
    print(f"  ví dụ token đầu: '{t0['word']}' k_old={t0['k_old']} -> "
          f"k_new={t0['k_new']}, p={[round(x, 3) for x in t0['probs']]}, r={t0['r']}")

    # --- giữ nguyên qua 20 vòng ---
    for _ in range(19):
        base.gibbs_sweep()
        traced.sweep_with_trace()
    assert base.z == traced.z, "Sau 20 vòng: assignments khác nhau"
    assert base.approx_log_likelihood() == traced.approx_log_likelihood()
    print("  sau 20 vòng: vẫn giống hệt")

    # bất biến bộ đếm
    traced.assert_counts_consistent()
    traced.assert_z_consistent()
    print("  assert sum(n_dk) == sum(n_kw) == sum(n_k) == tổng token: OK")
    print("  -> OK")
    return trace


def test_c_reproducible():
    """(c) Cùng seed -> cùng kết quả; seed khác -> khác kết quả."""
    hr("(c) Tính tái lập — cùng seed cho cùng kết quả")

    prep1 = preprocess_document(SAMPLE_TEXT_SUMMARIZE)
    prep2 = preprocess_document(SAMPLE_TEXT_SUMMARIZE)
    assert prep1["docs_tokens"] == prep2["docs_tokens"], "Tiền xử lý không tất định"
    print("  tiền xử lý: docs_tokens giống nhau "
          f"({len(prep1['docs_tokens'])} câu, {prep1['stats']['num_kept_tokens']} token)")

    r1 = summarize_document(SAMPLE_TEXT_SUMMARIZE, seed=42, iterations=60)
    r2 = summarize_document(SAMPLE_TEXT_SUMMARIZE, seed=42, iterations=60)
    j1 = json.dumps(r1, sort_keys=True, ensure_ascii=False)
    j2 = json.dumps(r2, sort_keys=True, ensure_ascii=False)
    assert j1 == j2, "Cùng seed nhưng kết quả khác nhau!"
    print(f"  pipeline: JSON giống hệt ({len(j1)} bytes)")

    r3 = summarize_document(SAMPLE_TEXT_SUMMARIZE, seed=7, iterations=60)
    assert r3["summary"]["text"] != r1["summary"]["text"] or \
        r3["scores"] != r1["scores"], "Seed khác mà kết quả y hệt (bất thường)"
    print("  seed=7: kết quả khác (đúng như mong đợi)")
    print("  -> OK")
    return r1


def test_d_log_likelihood():
    """(d) log-likelihood nhìn chung tăng theo số vòng."""
    hr("(d) log-likelihood ước lượng theo số vòng")

    res = summarize_document(SAMPLE_TEXT_SUMMARIZE, seed=42, iterations=60)
    lls = [h["log_likelihood"] for h in res["history"]]

    for i in (0, 1, 2, 5, 10, 20, 30, 40, 50, 59, 60):
        print(f"  vòng {i:>2}: {lls[i]}")

    assert len(lls) == 61, "Phải có 61 snapshot (khởi tạo + 60 vòng)"
    assert lls[-1] > lls[0], "log-likelihood cuối không lớn hơn ban đầu"

    # LL ước lượng phụ thuộc cấu hình z TỨC THỜI nên rung theo vòng; xu hướng
    # được đánh giá bằng trung bình 10 vòng đầu vs 10 vòng cuối.
    head = sum(lls[:10]) / 10
    tail = sum(lls[-10:]) / 10
    print(f"  trung bình 10 vòng đầu: {head:.2f}")
    print(f"  trung bình 10 vòng cuối: {tail:.2f}  (chênh {tail - head:+.2f})")
    assert tail > head, "Xu hướng tăng không rõ"

    best = max(lls)
    print(f"  giá trị cao nhất: {best} (vòng {lls.index(best)})")
    print("  -> OK (LL ước lượng rung theo cấu hình z, xem ghi chú lý thuyết)")
    return res


def test_e_preprocess_and_errors():
    """Tiền xử lý: tách câu đúng, xử lý lỗi thân thiện."""
    hr("Tiền xử lý — tách câu & xử lý lỗi")

    sents = split_sentences(
        "Giá xe tăng 3.5 triệu. Ông ấy nói v.v rằng tp. Hồ Chí Minh có 12 quận! "
        "Câu này bị\nngắt dòng giữa chừng.\nCâu cuối…"
    )
    print(f"  tách {len(sents)} câu:")
    for i, s in enumerate(sents, 1):
        print(f"    {i}. {s}")
    assert len(sents) == 4, "Tách sai số câu"
    assert "3.5" in sents[0], "Mất số thập phân"
    assert "v.v" in sents[1], "Cắt nhầm chữ viết tắt"
    assert "ngắt dòng giữa chừng" in sents[2], "Không nối được câu bị ngắt dòng"

    cases = [
        ("rỗng", "", "Vui lòng nhập"),
        ("quá ngắn", "Một. Hai.", "ít nhất 5 câu"),
        ("quá dài", "Câu một. " * 200, "quá dài"),
    ]
    for name, text, expect in cases:
        try:
            summarize_document(text)
            raise AssertionError(f"{name}: lẽ ra phải báo lỗi")
        except PreprocessError as e:
            assert expect in str(e), f"{name}: thông báo sai -> {e}"
            print(f"  lỗi [{name}]: {e}")

    # K lớn hơn số từ vựng
    try:
        summarize_document(SAMPLE_TEXT_SUMMARIZE, num_topics=4)
        print("  lỗi [K lớn]: (đoạn mẫu đủ từ vựng nên không lỗi — OK)")
    except ValueError as e:
        print(f"  lỗi [K lớn]: {e}")
    print("  -> OK")


def test_e_summary(res):
    """(e) In bản tóm tắt cuối của đoạn mẫu."""
    hr("(e) BẢN TÓM TẮT CUỐI CÙNG — đoạn mẫu (K=2, 60 vòng, seed=42, 3 câu)")

    print(f"  Thống kê: {res['stats']['num_sentences']} câu → "
          f"{res['stats']['num_kept_tokens']} token nội dung, "
          f"{res['stats']['vocab_size']} từ vựng, "
          f"bỏ {res['stats']['num_stopwords_removed']} stopword")
    print(f"  Chủ đề:")
    for k, label in enumerate(res["topics"]["labels"]):
        top = ", ".join(w for w, _ in res["topics"]["top_words"][k][:6])
        print(f"    {k + 1}. {label}   [{top}]")
    print(f"  Phân bố chủ đề toàn đoạn π = {res['topics']['pi']}")

    print(f"\n  Điểm từng câu (eligible):")
    for s in res["scores"]:
        mark = "✓ chọn" if s["sentence_index"] in res["mmr"]["selected"] else "  loại"
        if not s["eligible"]:
            mark = "— bỏ qua"
        print(f"    câu {s['sentence_index'] + 1:>2}: {s['score']:.4f}  "
              f"cos={s['cosine']:.3f}  p={s['token_prob']:.5f}  "
              f"hệ số dài={s['length_factor']}  {mark}")

    print(f"\n  Tóm tắt ({res['summary']['num_sentences_summary']}/"
          f"{res['summary']['num_sentences_original']} câu, "
          f"{res['summary']['num_words_original']} → "
          f"{res['summary']['num_words_summary']} từ, "
          f"nén {res['summary']['compression_ratio']}x):")
    for i, s in enumerate(res["summary"]["sentences"], 1):
        print(f"    {i}. {s['text']}")

    print(f"\n  Vì sao các câu khác bị loại:")
    for r in res["mmr"]["rejected"]:
        print(f"    câu {r['sentence_index'] + 1:>2}: {r['reason']}")

    print(f"\n  JSON payload: {res['meta']['json_bytes'] / 1024:.1f} KB, "
          f"trace vòng {res['meta']['traces_kept']}")


def main():
    print("KIỂM THỬ BACKEND — Tóm tắt dạng video (Gibbs tự cài đặt)")
    test_a_demo_unchanged()
    test_b_trace_matches()
    res_c = test_c_reproducible()
    res = test_d_log_likelihood()
    test_e_preprocess_and_errors()
    test_e_summary(res)

    hr("TẤT CẢ KIỂM THỬ ĐẠT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
