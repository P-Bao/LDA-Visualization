# TÀI LIỆU KỸ THUẬT: CÔNG THỨC CHẤM ĐIỂM VÀ CHỌN CÂU TÓM TẮT TỪ MÔ HÌNH LDA – GIBBS SAMPLING

Tài liệu này tổng hợp các công thức toán học đã được chuẩn hóa cho bước **Chấm điểm câu (Cảnh 9)** và **Chọn câu tóm tắt (Cảnh 10)** trong mô phỏng **Collapsed Gibbs Sampling LDA** (`core/summarizer_pipeline.py`), kèm theo đường dẫn trực tiếp tới các công bố khoa học chứa công thức.

---

## 1. Bảng Đối Chiếu Thay Thế Công Thức

| Bước xử lý | Công thức cũ trong Codebase (Đã xóa bỏ) | Công thức mới đã thay thế (Chuẩn công bố khoa học) | Bài báo khoa học tham chiếu |
| :--- | :--- | :--- | :--- |
| **Đầu vào hậu nghiệm từ Gibbs Sampling (Cảnh 6, 7, 8)** | Tính $\hat{\theta}_{d,k}$ và $\hat{\varphi}_{k,w}$ từ bộ đếm Gibbs nhưng chưa trích dẫn phương trình gốc. | Chuẩn hóa ký hiệu theo **Eq. 5, Eq. 6, Eq. 7**: $\hat{\varphi}_{k,w} = \frac{n_{k,w} + \beta}{n_k + V\beta}$ và $\hat{\theta}_{d,k} = \frac{n_{d,k} + \alpha}{n_d + K\alpha}$. | **Griffiths & Steyvers (PNAS, 2004)** |
| **Chấm điểm câu (Cảnh 9 — `score_sentences`)** | $\text{Score}(d) = \left(0.6 \cos(\theta_d, \pi) + 0.4 \bar{p}_d\right) \times \text{length\_factor}$ (phạt $\times 0.85$ khi $< 4$ từ, $\times 0.92$ khi $> 26$ từ). | **Xác suất sinh hậu nghiệm trung bình:** $\text{RawScore}(d) = \frac{1}{n_d} \sum_{w \in d} \sum_{k=1}^K \pi_k \hat{\theta}_{d,k} \hat{\varphi}_{k,w}$, chuẩn hóa $\text{Score}(d) = \frac{\text{RawScore}(d)}{\max_{d'} \text{RawScore}(d')} \in [0, 1]$. | **Griffiths & Steyvers (PNAS, 2004, Eq. 1)**; **Haghighi & Vanderwende (NAACL, 2009)**; **Nenkova & Vanderwende (2005)** |
| **Đo độ trùng lặp & Chọn câu (Cảnh 10 — `select_sentences_mmr`)** | Dùng độ tương đồng góc phẳng Euclid $\cos(\theta_d, \theta_j)$ trong công thức MMR. | **JSD-MMR trên đơn hình Dirichlet:** Dùng Phân kỳ Kullback-Leibler ($D_{KL}$) và Jensen-Shannon chuẩn hóa ($D_{JS}$): $\text{Sim}_{JS}(\hat{\theta}_d, \hat{\theta}_j) = 1 - D_{JS}(\hat{\theta}_d \parallel \hat{\theta}_j)$ đưa vào MMR ($\lambda = 0.7$). | **Blei, Ng & Jordan (JMLR, 2003, Eq. 5)**; **Hennig (RANLP, 2009)**; **Louis & Nenkova (EMNLP, 2009)**; **Carbonell & Goldstein (SIGIR, 1998)** |

---

## 2. Đầu Vào Từ Thuật Toán Collapsed Gibbs Sampling LDA

Sau khi chạy chuỗi Markov lấy mẫu Gibbs rút gọn (Collapsed Gibbs Sampling) theo phân phối có điều kiện đầy đủ (**Eq. 5**, Griffiths & Steyvers, 2004):

$$P(z_i = k \mid \mathbf{z}_{-i}, \mathbf{w}) \propto \frac{n_{-i, k}^{(w_i)} + \beta}{n_{-i, k}^{(\cdot)} + V\beta} \cdot \frac{n_{-i, k}^{(d_i)} + \alpha}{n_{-i, \cdot}^{(d_i)} + K\alpha}$$

Hệ thống thu được hai ma trận xác suất hậu nghiệm cho từng câu (văn bản con) $d \in \{1, \dots, D\}$ và từng từ vựng $w \in \{1, \dots, V\}$ trên $K$ chủ đề (**Eq. 6** và **Eq. 7**, Griffiths & Steyvers, 2004):

$$\hat{\varphi}_{k, w} = \frac{n_{k, w} + \beta}{n_k + V\beta}, \qquad \hat{\theta}_{d, k} = \frac{n_{d, k} + \alpha}{n_d + K\alpha}$$

Trong đó:
* $n_{k, w}$: Số lần từ $w$ được gán vào chủ đề $k$ trên toàn văn bản.
* $n_k = \sum_{w=1}^{V} n_{k, w}$: Tổng số từ được gán vào chủ đề $k$.
* $n_{d, k}$: Số từ trong câu $d$ được gán vào chủ đề $k$.
* $n_d = \sum_{k=1}^{K} n_{d, k}$: Tổng số từ nội dung (sau khi lọc stopword) của câu $d$.
* $\alpha, \beta$: Các siêu tham số tiên nghiệm Dirichlet đối xứng của phân phối chủ đề và phân phối từ vựng.

Từ phân phối chủ đề $\hat{\theta}_{d, k}$ của từng câu, **phân phối chủ đề toàn văn bản** $\pi = (\pi_1, \dots, \pi_K)$ được tính bằng trung bình có trọng số theo độ dài token nội dung $n_d$ của từng câu (Haghighi & Vanderwende, 2009):

$$\pi_k = \frac{\sum_{d=1}^{D} n_d \cdot \hat{\theta}_{d, k}}{\sum_{d=1}^{D} n_d}, \quad \text{với } \sum_{k=1}^{K} \pi_k = 1$$

---

## 3. Công Thức Chấm Điểm Câu (Cảnh 9 — Hàm `score_sentences`)

### 3.1. Công thức tự chế cũ đã loại bỏ
Xóa bỏ hoàn toàn công thức ghép tuyến tính tự đặt:

$$\text{Score}_{\text{cũ}}(d) = \left( 0.6 \times \cos(\theta_d, \pi) + 0.4 \times \frac{1}{n_d}\sum_{w \in d}\sum_{k=1}^K \pi_k \varphi_{k,w} \right) \times \text{length\_factor}(n_d)$$

cùng toàn bộ các hằng số tự chế `0.6`, `0.4`, `SHORT_SENTENCE_FACTOR = 0.85`, `LONG_SENTENCE_FACTOR = 0.92`.

### 3.2. Công thức chuẩn khoa học mới: Xác suất Sinh Hậu nghiệm Trung bình
Theo **Phương trình [Eq. 1]** của Griffiths & Steyvers (2004), xác suất sinh một từ $w_i$ dưới mô hình hỗn hợp chủ đề là:

$$P(w_i) = \sum_{k=1}^{K} P(w_i \mid z_i = k) P(z_i = k)$$

Khi đánh giá mức độ đại diện của câu $d$ đối với toàn văn bản, xác suất sinh hậu nghiệm của mỗi từ $w \in d$ được tính bằng cách kết hợp trọng số chủ đề toàn cục $\pi_k$, tỷ lệ chủ đề cục bộ của câu $\hat{\theta}_{d, k}$ (**Eq. 7**) và xác suất từ vựng trong chủ đề $\hat{\varphi}_{k, w}$ (**Eq. 6**). Điểm xác suất sinh trung bình của câu $d$ (chuẩn hóa theo số lượng từ nội dung $n_d$ theo mô hình SumBasic của Nenkova & Vanderwende, 2005) là:

$$\text{RawScore}(d) = \frac{1}{n_d} \sum_{w \in d} \sum_{k=1}^{K} \pi_k \cdot \hat{\theta}_{d, k} \cdot \hat{\varphi}_{k, w}$$

Đổi thứ tự lấy tổng theo chủ đề $k$, điểm của câu $d$ được phân rã tường minh thành tổng đóng góp của từng chủ đề $k \in \{1, \dots, K\}$ (biểu diễn trực tiếp trên thanh điểm phân đoạn ở Cảnh 9):

$$\text{RawScore}(d) = \sum_{k=1}^{K} \text{topic\_parts}_k(d), \quad \text{với } \text{topic\_parts}_k(d) = \pi_k \cdot \hat{\theta}_{d, k} \cdot \left( \frac{1}{n_d} \sum_{w \in d} \hat{\varphi}_{k, w} \right)$$

Để đồng nhất thang đo $[0, 1]$ với bước chọn câu đa dạng phía sau, điểm câu được chuẩn hóa theo câu có xác suất sinh cao nhất trong văn bản:

$$\text{Score}(d) = \frac{\text{RawScore}(d)}{\max_{d' \in \{1..D\}} \text{RawScore}(d')} \in [0, 1]$$

---

## 4. Công Thức Chọn Câu Đa Dạng Chủ Đề (Cảnh 10 — Hàm `select_sentences_mmr`)

### 4.1. Công thức cũ đã loại bỏ
Loại bỏ việc dùng độ tương đồng góc phẳng Euclid $\cos(\hat{\theta}_d, \hat{\theta}_j)$ giữa hai vector xác suất chủ đề.

### 4.2. Công thức chuẩn khoa học mới: JSD-MMR trên Đơn hình Chủ đề Dirichlet
Theo **Blei, Ng & Jordan (2003, Mục 3 & Mục 4.4)**, mỗi vector phân phối chủ đề của câu $\hat{\theta}_d = (\hat{\theta}_{d, 1}, \dots, \hat{\theta}_{d, K})$ là một điểm nằm trên **đơn hình chủ đề (topic simplex $\Delta^{K-1}$)** thỏa mãn $\hat{\theta}_{d, k} > 0$ và $\sum_{k=1}^K \hat{\theta}_{d, k} = 1$.

Trên đơn hình xác suất này, độ chênh lệch thông tin giữa hai phân phối chủ đề câu $\hat{\theta}_d$ và $\hat{\theta}_j$ được đo bằng **Phân kỳ Kullback-Leibler ($D_{KL}$)** (**Eq. 5**, Blei et al., 2003) và dạng đối xứng bị chặn chặt trong đoạn $[0, 1]$ của nó là **Phân kỳ Jensen-Shannon chuẩn hóa ($D_{JS}$)** (Lin, 1991; Louis & Nenkova, 2009; Hennig, 2009):

1. **Phân kỳ Kullback-Leibler ($D_{KL}$):**
   $$D_{KL}(P \parallel Q) = \sum_{k=1}^{K} P_k \ln \left( \frac{P_k}{Q_k} \right)$$

2. **Phân kỳ Jensen-Shannon chuẩn hóa về đoạn $[0, 1]$ ($D_{JS}$):**
   $$D_{JS}\left(\hat{\theta}_d \parallel \hat{\theta}_j\right) = \frac{1}{2 \ln 2} \left[ D_{KL}\left(\hat{\theta}_d \parallel M\right) + D_{KL}\left(\hat{\theta}_j \parallel M\right) \right] \in [0, 1], \quad \text{với } M = \frac{1}{2}\left(\hat{\theta}_d + \hat{\theta}_j\right)$$

3. **Độ tương đồng chủ đề trên đơn hình Dirichlet ($\text{Sim}_{JS}$):**
   $$\text{Sim}_{JS}\left(\hat{\theta}_d, \hat{\theta}_j\right) = 1 - D_{JS}\left(\hat{\theta}_d \parallel \hat{\theta}_j\right) \in [0, 1]$$

4. **Tiêu chuẩn chọn câu tuần tự JSD-MMR (Carbonell & Goldstein, 1998; Hennig, 2009):**
   Gọi $S$ là tập các câu tóm tắt đã chọn.
   * **Bước 1 ($S = \emptyset$):** Chọn câu hạt nhân có xác suất sinh hậu nghiệm cao nhất:
     $$d_1^* = \underset{d}{\arg\max} \, \text{Score}(d)$$
   * **Bước $t = 2, \dots, M$:** Chọn câu $d^* \notin S$ cực đại hóa hàm mục tiêu JSD-MMR (với $\lambda = 0.7$):
     $$\text{MMR}_{JS}(d) = \lambda \cdot \text{Score}(d) - (1 - \lambda) \max_{j \in S} \text{Sim}_{JS}\left(\hat{\theta}_d, \hat{\theta}_j\right)$$

Sau khi chọn đủ $M$ câu, tập câu trong $S$ được sắp xếp lại theo thứ tự xuất hiện gốc trong văn bản để tạo thành bản tóm tắt hoàn chỉnh (Cảnh 11).

---

## 5. Đường Dẫn Các Bài Báo Khoa Học Liên Quan Đến Chấm Điểm & Chọn Câu Bằng LDA – Gibbs

Dưới đây là danh sách các công bố khoa học chính thống sử dụng trực tiếp đầu ra của mô hình LDA – Gibbs Sampling để chấm điểm câu và chọn câu tóm tắt:

1. **Griffiths, T. L., & Steyvers, M. (PNAS, 2004) — *Finding scientific topics***
   * **Công thức liên quan:** Phương trình **[Eq. 1]** (Xác suất từ dưới hỗn hợp chủ đề $P(w_i) = \sum_{j=1}^T P(w_i \mid z_i=j)P(z_i=j)$), **[Eq. 5]** (Phân phối lấy mẫu Collapsed Gibbs Sampling), **[Eq. 6]** và **[Eq. 7]** (Ước lượng hậu nghiệm $\hat{\varphi}$ và $\hat{\theta}$ dùng làm đầu vào chấm điểm câu).
   * **Link DOI chính thức:** [https://doi.org/10.1073/pnas.0307752101](https://doi.org/10.1073/pnas.0307752101)
   * **Link toàn văn PNAS:** [https://www.pnas.org/doi/10.1073/pnas.0307752101](https://www.pnas.org/doi/10.1073/pnas.0307752101)

2. **Haghighi, A., & Vanderwende, L. (NAACL-HLT, 2009) — *Exploring Content Models for Multi-Document Summarization***
   * **Công thức liên quan:** Ước lượng phân phối chủ đề toàn cục $\pi$ bằng Collapsed Gibbs Sampling và lựa chọn câu tóm tắt trích xuất dựa trên xác suất sinh từ kết hợp phân kỳ Kullback-Leibler (Mục 3, trang 363–366).
   * **Link ACL Anthology:** [https://aclanthology.org/N09-1041/](https://aclanthology.org/N09-1041/)
   * **Link PDF trực tiếp:** [https://aclanthology.org/N09-1041.pdf](https://aclanthology.org/N09-1041.pdf)

3. **Arora, R., & Ravindran, B. (ACM SIGIR Workshop AND, 2008) — *Latent Dirichlet Allocation Based Multi-Document Summarization***
   * **Công thức liên quan:** Sử dụng trực tiếp LDA huấn luyện bằng Collapsed Gibbs Sampling để tính điểm trọng số của từng câu đối với từng chủ đề $k$ từ tích xác suất $\hat{\varphi}_{k, w}$ và $\hat{\theta}_{d, k}$ phục vụ trích xuất câu tóm tắt (Mục 3 & Mục 4, trang 93–95).
   * **Link DOI chính thức:** [https://doi.org/10.1145/1390749.1390764](https://doi.org/10.1145/1390749.1390764)

4. **Hennig, L. (RANLP, 2009) — *Topic-based Multi-Document Summarization with Probabilistic Latent Semantic Analysis***
   * **Công thức liên quan:** Chấm điểm câu dựa trên phân phối chủ đề và kết hợp trực tiếp độ đo **Phân kỳ Jensen-Shannon ($D_{JS}$)** vào thuật toán chọn câu **MMR** để loại bỏ câu trùng lặp chủ đề (Mục 3.1 & Mục 3.2, trang 145–146).
   * **Link ACL Anthology:** [https://aclanthology.org/R09-1027/](https://aclanthology.org/R09-1027/)
   * **Link PDF trực tiếp:** [https://aclanthology.org/R09-1027.pdf](https://aclanthology.org/R09-1027.pdf)

5. **Louis, A., & Nenkova, A. (EMNLP, 2009) — *Automatically Evaluating Content Selection in Summarization without Human Models***
   * **Công thức liên quan:** Công thức tính **Phân kỳ Jensen-Shannon ($D_{JS}$)** từ trung bình hai phân kỳ Kullback-Leibler ($D_{KL}$) để đo độ tương đồng phân phối xác suất giữa câu tóm tắt và toàn văn bản gốc (Mục 3, trang 307–308).
   * **Link ACL Anthology:** [https://aclanthology.org/D09-1032/](https://aclanthology.org/D09-1032/)
   * **Link PDF trực tiếp:** [https://aclanthology.org/D09-1032.pdf](https://aclanthology.org/D09-1032.pdf)

6. **Nenkova, A., & Vanderwende, L. (Microsoft Research, 2005) — *The Impact of Frequency on Summarization (SumBasic)***
   * **Công thức liên quan:** Công thức chấm điểm câu bằng trung bình cộng xác suất sinh của các từ trong câu ($\frac{1}{n_d} \sum_{w \in d} P(w)$) để chuẩn hóa công bằng giữa câu ngắn và câu dài.
   * **Link Microsoft Research:** [https://www.microsoft.com/en-us/research/publication/the-impact-of-frequency-on-summarization/](https://www.microsoft.com/en-us/research/publication/the-impact-of-frequency-on-summarization/)
   * **Link PDF trực tiếp:** [https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2005-101.pdf](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-2005-101.pdf)

7. **Carbonell, J., & Goldstein, J. (ACM SIGIR, 1998) — *The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries***
   * **Công thức liên quan:** Công thức gốc của thuật toán **Maximal Marginal Relevance (MMR)** cân bằng giữa độ liên quan của câu và độ trùng lặp lớn nhất với các câu đã chọn theo hệ số $\lambda = 0.7$ (Mục 2, Công thức 1, trang 335).
   * **Link DOI chính thức:** [https://doi.org/10.1145/290941.291025](https://doi.org/10.1145/290941.291025)
   * **Link PDF trực tiếp:** [https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf](https://www.cs.cmu.edu/~jgc/publication/The_Use_MMR_Diversity_Based_LTMIR_1998.pdf)