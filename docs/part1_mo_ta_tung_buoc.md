# Mô tả Từng bước Thuật toán LDA & Tóm tắt Văn bản (Phần 1 & 1+)

> Tài liệu kỹ thuật bàn giao dành cho thành viên phụ trách viết báo cáo lý thuyết (**Phi**), thuyết trình (**Cương**) và thiết kế slide (**Phương**).  
> Toàn bộ số liệu trong tài liệu này được trích xuất trực tiếp từ các lần chạy thật nghiệm thu của hệ thống, tuân thủ nguyên tắc trung thực khoa học.

---

## 1. Bảng ánh xạ 6 Giai đoạn Lý thuyết → 11 Cảnh Mô phỏng Player

Hệ thống mô phỏng "Tóm tắt dạng video" phân rã toàn bộ quy trình suy luận từ văn bản thô tới bản tóm tắt trích xuất thành **6 giai đoạn lớn**, hiển thị trực quan qua **11 cảnh động**:

| Giai đoạn (Thanh Stepper) | Cảnh | File / Hàm phụ trách | Công thức / Quy tắc kỹ thuật | Điểm mấu chốt khi thuyết trình |
|---|---|---|---|---|
| **1. Tiền xử lý** | **Cảnh 1: Văn bản gốc** | `core/summarizer_pipeline.py`<br>`summarize_document()` | Thống kê số từ thô, số câu, từ vựng ban đầu. | Người dùng nhập văn bản tuỳ ý (hoặc chọn preset). Hệ thống chuẩn bị dữ liệu đầu vào. |
| | **Cảnh 2: Tách câu** | `core/summarizer_preprocess.py`<br>`split_sentences()` | Tách theo dấu kết câu (`.`, `!`, `?`, `…`) hoặc ngắt dòng. Bảo vệ số thực (`3.5`), viết tắt (`tp.`, `v.v.`). | **Mỗi câu trở thành một "document" nhỏ** của LDA. Càng nhiều câu, tín hiệu đồng xuất hiện từ càng rõ. |
| | **Cảnh 3: Tách từ & làm sạch** | `core/summarizer_preprocess.py`<br>`tokenize_sentence()`, `_match_compound()` | Thuật toán **Longest Matching** (tối đa 4 âm tiết) dựa trên `core/vi_lexicon.py`. Lọc bỏ stopword, số, từ $<2$ ký tự (`short`). | Vì sao bỏ stopword: Chúng có tần suất cao ở mọi câu, không mang thông tin chủ đề. Từ ghép cần gom lại để không mất ngữ nghĩa. |
| **2. Từ điển & Ma trận đếm** | **Cảnh 4: Từ điển & Heatmap** | `core/summarizer_preprocess.py`<br>`build_count_matrix()` | Gom tập từ vựng duy nhất $V$. Tạo ma trận tần suất $n(d, w)$ (Bag-of-Words: số câu $\times$ kích thước từ vựng). | Biểu diễn văn bản dưới dạng không gian vector Bag-of-Words. Ô heatmap đậm thể hiện từ xuất hiện nhiều lần trong câu. |
| **3. Chạy LDA (Gibbs)** | **Cảnh 5: Khởi tạo Gibbs** | `core/trace_lda.py`<br>`TracedGibbsLDA.__init__()` | Gán ngẫu nhiên $z_{di} \in \{0, \dots, K-1\}$. Khởi tạo 3 bộ đếm: $n(d, k)$, $n(k, w)$, $n(k)$. | Điểm xuất phát hoàn toàn ngẫu nhiên và tùy ý. Thuật toán sẽ liên tục tự điều chỉnh qua các vòng lấy mẫu. |
| | **Cảnh 6: Gibbs chi tiết vòng 1** | `core/trace_lda.py`<br>`sweep_with_trace()` | $P(z=k) \propto (n_{dk}^{\neg} + \alpha) \cdot \frac{n_{kw}^{\neg} + \beta}{n_k^{\neg} + V\beta}$. Lấy mẫu lại qua số ngẫu nhiên $r \in [0, 1)$. | **Rút token đang xét ra khỏi bộ đếm** trước khi tính xác suất (tránh tự bỏ phiếu cho chính mình). |
| | **Cảnh 7: Gibbs tăng tốc vòng $2 \to N$** | `core/trace_lda.py`<br>`sweep()`, `snapshot()` | Lặp $N$ vòng (mặc định 30). Ước lượng log-likelihood qua từng vòng. Cập nhật phân bố $\theta$ từng câu và top 4 từ mỗi chủ đề. | Kéo thanh trượt để thấy mô hình hội tụ: các câu cùng chủ đề gom về cùng màu, top từ khóa dần định hình rõ rệt. |
| **4. Phân bố chủ đề** | **Cảnh 8: Kết quả chủ đề** | `core/trace_lda.py`<br>`theta()`, `phi()`, tính $\pi$ | $\theta_{dk} = \frac{n_{dk} + \alpha}{n_d + K\alpha}$, $\phi_{kw} = \frac{n_{kw} + \beta}{n_k + V\beta}$.<br>$\pi_k = \frac{\sum_d n_d \cdot \theta_{dk}}{\sum_d n_d}$. | Ma trận $\Phi$ định nghĩa chủ đề qua các từ có trọng số lớn nhất. $\pi$ là phân bố chủ đề đại diện cho toàn bộ đoạn văn. |
| **5. Chấm điểm & Chọn câu** | **Cảnh 9: Chấm điểm câu** | `core/summarizer_pipeline.py`<br>`score_sentences()` | $\text{raw} = 0.6 \cdot \cos(\theta_d, \pi) + 0.4 \cdot \bar{p}_d$.<br>$\text{score} = \text{raw} \cdot \text{length\_factor}$. | Đánh giá câu đại diện: vừa sát chủ đề toàn bài ($\cos$), vừa chứa từ có xác suất sinh cao ($\bar{p}$), phạt câu quá ngắn/dài. |
| | **Cảnh 10: Chọn câu MMR** | `core/summarizer_pipeline.py`<br>`select_sentences_mmr()` | $\text{MMR} = \lambda \cdot \text{Rel}(d) - (1-\lambda) \cdot \max_{s \in S} \cos(\theta_d, \theta_s)$ với $\lambda = 0.7$. | Tránh trùng lặp nội dung: Chọn câu điểm cao nhưng phạt nặng nếu nội dung tương đồng với câu đã chọn trước đó. |
| **6. Bản tóm tắt** | **Cảnh 11: Ghép tóm tắt** | `core/summarizer_pipeline.py`<br>`summarize_document()` | Sắp xếp các câu được chọn theo **thứ tự xuất hiện ban đầu**. Tính tỉ lệ nén từ. | Bản tóm tắt giữ nguyên trật tự mạch văn gốc, đảm bảo tính liên kết và tự nhiên khi đọc. |

---

## 2. Bảng Tham số Mô hình & Ý nghĩa Thực tế

| Tham số | Ý nghĩa lý thuyết | Mặc định chung (BE-1) | Giá trị Preset "toy" (8 câu) | Ghi chú vận hành |
|---|---|---|---|---|
| $K$ | Số lượng chủ đề ẩn cần trích xuất | $2$ | $2$ | Hỗ trợ từ $2$ đến $4$ trên giao diện mô phỏng. |
| $\alpha$ | Dirichlet Hyperparameter cho phân bố tài liệu–chủ đề $\theta$ | $0.1$ | $0.1$ | $\alpha < 1$ khuyến khích mỗi câu tập trung vào một số ít chủ đề chính. |
| $\beta$ | Dirichlet Hyperparameter cho phân bố chủ đề–từ vựng $\phi$ | $0.01$ | $0.01$ | $\beta \ll 1$ khuyến khích mỗi chủ đề tập trung vào các từ đặc trưng riêng biệt. |
| $\text{iterations}$ | Số vòng lặp lấy mẫu Gibbs | **$30$** (đã tối ưu theo BE-1) | $30$ | Đủ để đồ thị log-likelihood hội tụ ổn định, thời gian chạy $<0.5$s. |
| $\text{seed}$ | Hạt ngẫu nhiên khởi tạo | $42$ | $42$ | Giữ kết quả tái lập tuyệt đối $100\%$ giữa các lần demo. |
| $n_{\text{sentences}}$ | Số câu chọn đưa vào bản tóm tắt | $3$ | $2$ | Với preset 8 câu (2 chủ đề), chọn 2 câu (mỗi chủ đề 1 câu đại diện). |
| $\lambda$ (MMR) | Trọng số cân bằng độ liên quan vs chống trùng lặp | $0.7$ | $0.7$ | Ưu tiên độ liên quan ($70\%$), dành $30\%$ phạt tương đồng ý. |

---

## 3. Ví dụ Tính tay Bước Lấy mẫu Gibbs (3 Token đầu tiên ở Vòng 1)

Số liệu kiểm chứng chạy trên **Preset "Dữ liệu nhỏ: 8 câu, 2 chủ đề"** ($K=2, \alpha=0.1, \beta=0.01, V=37$ từ vựng, seed $42$).  
*Đã được kiểm chứng và khớp tuyệt đối với trace thực nghiệm của `core/trace_lda.py`.*

Công thức lấy mẫu cho token vị trí $i$ trong câu $d$ có từ vựng $w$:
$$P(z = k) \propto (n_{dk}^{\neg} + \alpha) \cdot \frac{n_{kw}^{\neg} + \beta}{n_k^{\neg} + V\beta}$$
Trong đó ký hiệu $^{\neg}$ biểu thị bộ đếm sau khi đã **trừ bớt** token đang xét.

### Token 1: Từ `"đội bóng"` (Câu 1 / doc 0, vị trí 0)
- Trạng thái trước khi xét: $k_{\text{old}} = 0$. Rút token ra khỏi bộ đếm chủ đề $0$:
  - $n_{dk} = [2, 1]$ (câu 0 còn 2 từ chủ đề 0, 1 từ chủ đề 1).
  - $n_{kw} = [1, 0]$ (từ "đội bóng" xuất hiện 1 lần ở k=0, 0 lần ở k=1 trong toàn bộ ngữ liệu).
  - $n_k = [30, 18]$ (tổng số từ của chủ đề 0 là 30, chủ đề 1 là 18).
- Mẫu số smoothing: $\text{denom}_0 = 30 + 37 \times 0.01 = 30.37$; $\text{denom}_1 = 18 + 37 \times 0.01 = 18.37$.
- Tính giá trị trọng số $\text{raw}$:
  - $k=0: (2 + 0.1) \times \frac{1 + 0.01}{30.37} = 2.1 \times 0.0332565 = \mathbf{0.06983866}$
  - $k=1: (1 + 0.1) \times \frac{0 + 0.01}{18.37} = 1.1 \times 0.00054437 = \mathbf{0.00059880}$
- Chuẩn hoá xác suất: $\text{Tổng} = 0.07043746$.
  - $P(k=0) = \frac{0.06983866}{0.07043746} = \mathbf{0.991499}$ ($99.15\%$)
  - $P(k=1) = \frac{0.00059880}{0.07043746} = \mathbf{0.008501}$ ($0.85\%$)
- Lấy mẫu: Số ngẫu nhiên sinh ra $r = 0.866484$. Vì $r < P(k=0)$ ($0.866484 < 0.991499$) $\to$ **Chọn $k_{\text{new}} = 0$** (Giữ nguyên chủ đề $0$).

---

### Token 2: Từ `"thi đấu"` (Câu 1 / doc 0, vị trí 1)
- Trạng thái trước khi xét: $k_{\text{old}} = 0$. Rút token ra khỏi bộ đếm:
  - $n_{dk} = [2, 1]$, $n_{kw} = [1, 0]$, $n_k = [30, 18]$.
- Tính giá trị trọng số $\text{raw}$:
  - $k=0: (2 + 0.1) \times \frac{1 + 0.01}{30.37} = \mathbf{0.06983866}$
  - $k=1: (1 + 0.1) \times \frac{0 + 0.01}{18.37} = \mathbf{0.00059880}$
- Chuẩn hoá xác suất: $P(k=0) = \mathbf{0.991499}$, $P(k=1) = \mathbf{0.008501}$.
- Lấy mẫu: Số ngẫu nhiên sinh ra $r = 0.380126 < 0.991499 \to$ **Chọn $k_{\text{new}} = 0$** (Giữ nguyên chủ đề $0$).

---

### Token 3: Từ `"bóng đá"` (Câu 1 / doc 0, vị trí 2)
- Trạng thái trước khi xét: $k_{\text{old}} = 1$. Rút token ra khỏi bộ đếm chủ đề $1$:
  - $n_{dk} = [3, 0]$ (câu 0 có 3 từ gán chủ đề 0, 0 từ gán chủ đề 1).
  - $n_{kw} = [2, 0]$ (từ "bóng đá" có 2 từ khác gán k=0, 0 từ gán k=1).
  - $n_k = [31, 17]$.
- Mẫu số smoothing: $\text{denom}_0 = 31 + 0.37 = 31.37$; $\text{denom}_1 = 17 + 0.37 = 17.37$.
- Tính giá trị trọng số $\text{raw}$:
  - $k=0: (3 + 0.1) \times \frac{2 + 0.01}{31.37} = 3.1 \times 0.06407396 = \mathbf{0.19862926}$
  - $k=1: (0 + 0.1) \times \frac{0 + 0.01}{17.37} = 0.1 \times 0.00057571 = \mathbf{0.00005757}$
- Chuẩn hoá xác suất: $\text{Tổng} = 0.19868683$.
  - $P(k=0) = \mathbf{0.999710}$ ($99.97\%$)
  - $P(k=1) = \mathbf{0.000290}$ ($0.03\%$)
- Lấy mẫu: Số ngẫu nhiên $r = 0.453410 < 0.999710 \to$ **Chọn $k_{\text{new}} = 0$** (**ĐỔI CHỦ ĐỀ: từ $1 \to 0$!**).
- *Ý nghĩa trực quan*: Từ "bóng đá" khi khởi tạo bị gán nhầm vào chủ đề công nghệ ($k=1$), qua bước lấy mẫu có điều kiện đã được kéo về chủ đề thể thao ($k=0$) với xác suất áp đảo $99.97\%$.

---

## 4. Các Lưu ý Khoa học & Trung thực Kỹ thuật

1. **Về đường cong Log-Likelihood**:
   - Giá trị log-likelihood hiển thị ở Cảnh 7 và đồ thị hội tụ là **log-likelihood ước lượng (approximate log-likelihood)** tính từ cấu hình snapshot $\theta$ và $\phi$ của vòng lặp đó: $\sum_d \sum_w c(d,w) \ln \left(\sum_k \theta_{dk}\phi_{kw}\right)$.
   - Nó phản ánh trực quan xu hướng mô hình khớp dần với ngữ liệu (tăng từ $-170.9$ lên $-144.5$), **không phải** là log-likelihood tích phân đầy đủ (marginal log-likelihood) của bài toán suy luận Bayes chuẩn.

2. **Về tỉ lệ đóng góp của thành phần xác suất từ ($p$) ở Cảnh 9**:
   - Trong công thức chấm điểm: $\text{score} = (0.6 \cdot \cos + 0.4 \cdot \bar{p}) \times \text{length\_factor}$.
   - Đo đạc thực nghiệm thực tế cho thấy: $\cos \in [0.7, 1.0]$ trong khi xác suất trung bình của từ $\bar{p} \in [0.01, 0.03]$. Do đó, ở chế độ mặc định, thành phần $0.4 \cdot \bar{p}$ thực tế chỉ đóng góp **$\approx 2.75\%$** vào tổng điểm thô của câu; điểm số chủ yếu được quyết định bởi độ tương đồng chủ đề $\cos$.
   - Nếu bật cờ tuỳ chọn `normalize_token_prob=True` (đã bổ sung ở BE-5), $\bar{p}$ được chuẩn hoá theo giá trị cực đại $\frac{\bar{p}}{\max \bar{p}}$, đưa tỉ lệ đóng góp của thành phần xác suất lên mức thực chất hơn ($\approx 25-35\%$).

3. **Khác biệt cốt lõi giữa Phần 1 và Phần 2/3**:
   - **Phần 1 & 1+**: Cài đặt thuật toán **Collapsed Gibbs Sampling** thủ công (thuần Python), theo dõi sự thay đổi của từng token đơn lẻ. Phù hợp cho giảng dạy, minh họa cơ chế lấy mẫu Monte Carlo trên văn bản ngắn ($\le 300$ từ).
   - **Phần 2 & 3**: Sử dụng thư viện **Gensim** với thuật toán **Online Variational Bayes (suy luận biến phân)**. Cùng giải bài toán LDA nhưng sử dụng phương pháp tối ưu hóa hàm mục tiêu thay vì lấy mẫu ngẫu nhiên, cho phép xử lý quy mô lớn hàng nghìn bài báo một cách nhanh chóng.

4. **Về cơ chế tách từ tiếng Việt của Player**:
   - Player chạy thuần Python không phụ thuộc C-extension hay thư viện ngoài (`underthesea`, `pyvi`).
   - Quá trình ghép từ dựa trên từ điển chọn lọc `core/vi_lexicon.py` theo nguyên tắc Longest Match. Các từ ghép mới ngoài từ điển sẽ được giữ ở dạng từ đơn.
