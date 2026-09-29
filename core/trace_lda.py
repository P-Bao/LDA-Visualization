# -*- coding: utf-8 -*-
"""
trace_lda.py
------------
Lớp TracedGibbsLDA — mở rộng GibbsLDA (core/gibbs_lda.py) để ghi lại
TỪNG BƯỚC của thuật toán, phục vụ trang "Tóm tắt dạng video".

NGUYÊN TẮC BẤT DI BẤT DỊCH:
  - core/gibbs_lda.py KHÔNG bị sửa. Demo 8 câu cũ (route /part1) chạy y hệt.
  - sweep_with_trace() lặp lại ĐÚNG logic của gibbs_sweep(), kể cả thứ tự
    và số lần gọi self.rng.random(), nên với cùng seed cho ra CÙNG kết quả.

Bổ sung:
  sweep_with_trace() : 1 vòng Gibbs có ghi lại mọi trạng thái trung gian
  phi_full()         : ma trận K x V đầy đủ (dùng cho chấm điểm câu)
  topic_labels()     : nhãn 2-3 từ đứng đầu mỗi chủ đề
"""

from core.gibbs_lda import GibbsLDA


class TracedGibbsLDA(GibbsLDA):
    """GibbsLDA có trace. Kế thừa nguyên vẹn __init__/theta/phi/snapshot."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_trace = []

    # ------------------------------------------------------------------
    # 1. VÒNG GIBBS CÓ GHI LẠI TỪNG TOKEN
    # ------------------------------------------------------------------
    def sweep_with_trace(self):
        """
        Giống hệt GibbsLDA.gibbs_sweep() nhưng ghi lại trạng thái sau khi
        "rút" token khỏi bộ đếm: xác suất chưa chuẩn hoá (left*right),
        xác suất đã chuẩn hoá, số r rút được, chủ đề mới, và các bộ đếm.

        Danh sách trả về (mỗi phần tử = 1 token) gồm:
            d, i            : chỉ số văn bản (doc trong LDA) và vị trí từ
            word            : từ (dạng chuỗi gốc)
            k_old           : chủ đề cũ (trước khi rút)
            n_dk            : [n_dk[d][k] cho mọi k] SAU KHI rút
            n_kw            : [n_kw[k][w] cho mọi k] SAU KHI rút
            n_k             : [n_k[k] cho mọi k] SAU KHI rút
            left            : [n_dk[d][k] + alpha]
            right           : [(n_kw[k][w] + beta) / (n_k[k] + V*beta)]
            raw             : [left[k] * right[k]]  (chưa chuẩn hoá)
            probs           : [raw[k] / sum(raw)]    (đã chuẩn hoá)
            r               : số ngẫu nhiên rút từ self.rng.random()
            k_new           : chủ đề được gán mới
            changed         : k_new != k_old
        """
        K = self.num_topics
        trace = []

        for d, doc in enumerate(self.docs):
            for i, w in enumerate(doc):
                k_old = self.z[d][i]

                # --- Bước 1: rút gán chủ đề hiện tại ra khỏi bộ đếm (giống hệt
                #     GibbsLDA.gibbs_sweep)
                self.n_dk[d][k_old] -= 1
                self.n_kw[k_old][w] -= 1
                self.n_k[k_old] -= 1

                # --- Số đếm SAU KHI rút (ảnh chụp cho giao diện)
                n_dk_after = list(self.n_dk[d])
                n_kw_after = [self.n_kw[k][w] for k in range(K)]
                n_k_after = list(self.n_k)

                # --- Bước 2: tính xác suất có điều kiện
                left = [
                    (self.n_dk[d][k] + self.alpha) for k in range(K)
                ]
                right = [
                    (self.n_kw[k][w] + self.beta) / (self.n_k[k] + self.V * self.beta)
                    for k in range(K)
                ]
                raw = [left[k] * right[k] for k in range(K)]
                total = sum(raw)
                probs = [p / total for p in raw]

                # --- Bước 3: lấy mẫu (ĐÚNG 1 lần gọi rng.random() như lớp gốc,
                #     cùng thứ tự duyệt -> cùng kết quả với gibbs_sweep())
                r = self.rng.random()
                cum = 0.0
                k_new = K - 1
                for k, p in enumerate(probs):
                    cum += p
                    if r <= cum:
                        k_new = k
                        break

                # --- Bước 4: cập nhật bộ đếm
                self.z[d][i] = k_new
                self.n_dk[d][k_new] += 1
                self.n_kw[k_new][w] += 1
                self.n_k[k_new] += 1

                trace.append(
                    {
                        "d": d,
                        "i": i,
                        "word": self.vocab[w],
                        "k_old": k_old,
                        "n_dk": n_dk_after,
                        "n_kw": n_kw_after,
                        "n_k": n_k_after,
                        "left": [round(v, 6) for v in left],
                        "right": [round(v, 8) for v in right],
                        "raw": [round(v, 10) for v in raw],
                        "probs": [round(p, 6) for p in probs],
                        "r": round(r, 6),
                        "k_new": k_new,
                        "changed": k_new != k_old,
                    }
                )

        self.iteration += 1
        self.last_trace = trace
        return trace

    # ------------------------------------------------------------------
    # 2. MA TRẬN PHI ĐẦY ĐỦ (K x V)
    # ------------------------------------------------------------------
    def phi_full(self):
        """
        Ma trận xác suất chủ đề-từ đầy đủ: phi[k][w] = (n_kw[k][w]+beta)/(n_k[k]+V*beta)
        (giống hệt cách approx_log_likelihood() tính nội bộ, nhưng tách ra
        để dùng cho việc chấm điểm câu).
        """
        K = self.num_topics
        phi = []
        for k in range(K):
            denom = self.n_k[k] + self.V * self.beta
            phi.append(
                [(self.n_kw[k][w] + self.beta) / denom for w in range(self.V)]
            )
        return phi

    # ------------------------------------------------------------------
    # 3. NHÃN CHỦ ĐỀ (2-3 từ đứng đầu)
    # ------------------------------------------------------------------
    def topic_labels(self, topn=3):
        """
        Sinh nhãn ngắn cho mỗi chủ đề từ top từ phân biệt nhất.

        Cách chọn: xếp các từ theo phi giảm dần, bỏ các từ đã xuất hiện ở
        chủ đề trước (để nhãn các chủ đề khác nhau), rồi lấy tối đa topn từ.
        """
        labels = []
        used = set()
        for topic in self.phi(topn=max(topn * 3, 8)):
            picked = []
            for word, _prob in topic:
                if word in used:
                    continue
                picked.append(word)
                used.add(word)
                if len(picked) >= topn:
                    break
            labels.append(" · ".join(picked) if picked else "chủ đề rỗng")
        return labels

    # ------------------------------------------------------------------
    # 4. KIỂM TRA BẤT BIẾN (chỉ bật khi dev)
    # ------------------------------------------------------------------
    def assert_counts_consistent(self):
        """
        Kiểm tra bất biến của Gibbs sampling:
            tổng n_dk == tổng n_kw == tổng n_k == tổng số token trong corpus.
        """
        total_tokens = sum(self.n_d)
        sum_dk = sum(sum(row) for row in self.n_dk)
        sum_kw = sum(sum(row) for row in self.n_kw)
        sum_k = sum(self.n_k)
        assert sum_dk == total_tokens, f"sum(n_dk)={sum_dk} != {total_tokens}"
        assert sum_kw == total_tokens, f"sum(n_kw)={sum_kw} != {total_tokens}"
        assert sum_k == total_tokens, f"sum(n_k)={sum_k} != {total_tokens}"
        return True

    def assert_z_consistent(self):
        """
        Kiểm tra z[d][i] khớp với các bộ đếm:
        n_dk[d][k] = số token trong doc d có z = k, và n_kw[k][w] tương ứng.
        """
        for d, doc in enumerate(self.docs):
            for k in range(self.num_topics):
                n = sum(1 for kk in self.z[d] if kk == k)
                assert self.n_dk[d][k] == n, f"n_dk[{d}][{k}] sai"
        for k in range(self.num_topics):
            for w in range(self.V):
                n = sum(
                    1
                    for d, doc in enumerate(self.docs)
                    for i, ww in enumerate(doc)
                    if ww == w and self.z[d][i] == k
                )
                assert self.n_kw[k][w] == n, f"n_kw[{k}][{w}] sai"
        return True
