# -*- coding: utf-8 -*-
"""
gibbs_lda.py
------------
CÀI ĐẶT LDA TỪ ĐẦU (không dùng gensim/sklearn) bằng phương pháp
Collapsed Gibbs Sampling, dùng riêng cho PHẦN 1 — MÔ PHỎNG THUẬT TOÁN.

Mục tiêu của file này không phải là hiệu năng, mà là để MỌI BƯỚC của
thuật toán đều lộ ra ngoài (trạng thái gán chủ đề cho từng từ, các ma
trận đếm, phân bố theta/phi) để giao diện web có thể "phát lại" từng
vòng lặp cho người dùng xem.

Ý tưởng thuật toán (nhắc lại):
  - Sinh dữ liệu giả định: mỗi văn bản là một phân bố trộn (mixture) của
    K chủ đề (theta_d), mỗi chủ đề là một phân bố xác suất trên từ vựng (phi_k).
  - Ta không biết theta, phi, và cũng không biết mỗi từ trong văn bản
    sinh ra từ chủ đề nào (biến ẩn z). Collapsed Gibbs sampling ước lượng
    z bằng cách, ở mỗi bước, LẦN LƯỢT xét từng từ, "rút" gán chủ đề hiện
    tại của nó ra khỏi các bộ đếm, rồi lấy mẫu lại chủ đề mới theo xác suất
    có điều kiện:

        P(z_i = k | ...) ∝ (n_{d,k}^{-i} + alpha) * (n_{k,w_i}^{-i} + beta)
                            / (n_k^{-i} + V * beta)

    trong đó:
      n_{d,k}  = số từ trong văn bản d đang được gán chủ đề k
      n_{k,w}  = số lần từ w được gán chủ đề k (toàn corpus)
      n_k      = tổng số từ được gán chủ đề k (toàn corpus)
      V        = kích thước từ vựng
      alpha, beta = hệ số Dirichlet prior (càng nhỏ thì phân bố càng "thưa")

  - Lặp lại nhiều vòng (sweep) trên toàn bộ từ, các bộ đếm sẽ dần hội tụ
    về một cấu hình chủ đề ổn định, phản ánh các chủ đề tiềm ẩn trong dữ liệu.
"""

import random
from collections import Counter


class GibbsLDA:
    def __init__(self, docs_tokens, num_topics=2, alpha=0.1, beta=0.01, seed=42):
        """
        docs_tokens: list các văn bản, mỗi văn bản là list token (chuỗi) đã tiền xử lý.
        """
        self.rng = random.Random(seed)
        self.num_topics = num_topics
        self.alpha = alpha
        self.beta = beta

        # Xây từ vựng
        vocab = sorted({tok for doc in docs_tokens for tok in doc})
        self.vocab = vocab
        self.word2id = {w: i for i, w in enumerate(vocab)}
        self.V = len(vocab)

        # Chuyển văn bản sang dạng id
        self.docs = [[self.word2id[tok] for tok in doc] for doc in docs_tokens]
        self.docs_tokens = docs_tokens  # giữ bản gốc để hiển thị
        self.D = len(self.docs)
        K = self.num_topics

        # Bộ đếm
        self.n_dk = [[0] * K for _ in range(self.D)]   # văn bản d - chủ đề k
        self.n_kw = [[0] * self.V for _ in range(K)]   # chủ đề k - từ w
        self.n_k = [0] * K                              # tổng số từ của chủ đề k
        self.n_d = [len(doc) for doc in self.docs]       # tổng số từ của văn bản d

        # Gán chủ đề khởi tạo NGẪU NHIÊN cho từng từ (bước 0 của thuật toán)
        self.z = []  # z[d][i] = chủ đề hiện tại của từ thứ i trong văn bản d
        for d, doc in enumerate(self.docs):
            z_doc = []
            for w in doc:
                k = self.rng.randrange(K)
                z_doc.append(k)
                self.n_dk[d][k] += 1
                self.n_kw[k][w] += 1
                self.n_k[k] += 1
            self.z.append(z_doc)

        self.iteration = 0

    def _sample_topic(self, d, i, w):
        """Lấy mẫu lại chủ đề cho từ thứ i trong văn bản d (đã bị 'rút' khỏi bộ đếm)."""
        K = self.num_topics
        probs = []
        for k in range(K):
            left = (self.n_dk[d][k] + self.alpha)
            right = (self.n_kw[k][w] + self.beta) / (self.n_k[k] + self.V * self.beta)
            probs.append(left * right)
        total = sum(probs)
        probs = [p / total for p in probs]

        r = self.rng.random()
        cum = 0.0
        for k, p in enumerate(probs):
            cum += p
            if r <= cum:
                return k
        return K - 1  # phòng sai số float

    def gibbs_sweep(self):
        """Thực hiện MỘT vòng quét Gibbs sampling qua toàn bộ từ trong corpus."""
        for d, doc in enumerate(self.docs):
            for i, w in enumerate(doc):
                k_old = self.z[d][i]
                # Bước 1: "rút" gán chủ đề hiện tại ra khỏi bộ đếm
                self.n_dk[d][k_old] -= 1
                self.n_kw[k_old][w] -= 1
                self.n_k[k_old] -= 1

                # Bước 2: lấy mẫu chủ đề mới theo xác suất có điều kiện
                k_new = self._sample_topic(d, i, w)

                # Bước 3: cập nhật lại bộ đếm với chủ đề mới
                self.z[d][i] = k_new
                self.n_dk[d][k_new] += 1
                self.n_kw[k_new][w] += 1
                self.n_k[k_new] += 1
        self.iteration += 1

    def theta(self):
        """Ước lượng phân bố văn bản-chủ đề (document-topic distribution)."""
        K = self.num_topics
        theta = []
        for d in range(self.D):
            row = [
                (self.n_dk[d][k] + self.alpha) / (self.n_d[d] + K * self.alpha)
                for k in range(K)
            ]
            theta.append(row)
        return theta

    def phi(self, topn=8):
        """Ước lượng phân bố chủ đề-từ (topic-word distribution), trả về top từ mỗi chủ đề."""
        K = self.num_topics
        result = []
        for k in range(K):
            denom = self.n_k[k] + self.V * self.beta
            word_probs = [
                (self.vocab[w], (self.n_kw[k][w] + self.beta) / denom)
                for w in range(self.V)
                if self.n_kw[k][w] > 0
            ]
            word_probs.sort(key=lambda x: x[1], reverse=True)
            result.append(word_probs[:topn])
        return result

    def approx_log_likelihood(self):
        """
        Ước lượng gần đúng "độ khớp" giữa mô hình hiện tại và dữ liệu:
        tổng log xác suất sinh ra mỗi từ dựa trên theta, phi hiện tại.
        Dùng để vẽ đường cong hội tụ minh hoạ (không phải log-likelihood
        chuẩn tắc tuyệt đối, nhưng đủ để thấy xu hướng tăng dần rồi ổn định).
        """
        import math

        theta = self.theta()
        phi_full = []
        K = self.num_topics
        for k in range(K):
            denom = self.n_k[k] + self.V * self.beta
            phi_full.append([(self.n_kw[k][w] + self.beta) / denom for w in range(self.V)])

        ll = 0.0
        for d, doc in enumerate(self.docs):
            for w in doc:
                p_word = sum(theta[d][k] * phi_full[k][w] for k in range(K))
                ll += math.log(max(p_word, 1e-12))
        return ll

    def snapshot(self):
        """Chụp lại toàn bộ trạng thái hiện tại để front-end hiển thị 1 bước."""
        return {
            "iteration": self.iteration,
            "assignments": [list(z_doc) for z_doc in self.z],
            "theta": [[round(v, 4) for v in row] for row in self.theta()],
            "phi": [
                [(w, round(p, 4)) for w, p in topic] for topic in self.phi(topn=8)
            ],
            "log_likelihood": round(self.approx_log_likelihood(), 3),
        }

    def run_and_record(self, num_iterations=15):
        """
        Chạy num_iterations vòng Gibbs sampling, LƯU LẠI trạng thái sau MỖI vòng.
        Trả về danh sách snapshot (kể cả snapshot ban đầu ở vị trí 0) để giao diện
        web có thể tua qua lại xem thuật toán "học" dần dần như thế nào.
        """
        history = [self.snapshot()]
        for _ in range(num_iterations):
            self.gibbs_sweep()
            history.append(self.snapshot())
        return history
