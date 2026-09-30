# LDA cho văn bản tiếng Việt — Mô phỏng · Tóm tắt Video · Ứng dụng · Thử nghiệm

Dự án Bài tập lớn môn **Phân tích & Khai phá dữ liệu văn bản**: Nghiên cứu, tự cài đặt và ứng dụng mô hình **Latent Dirichlet Allocation (LDA)** trên ngữ liệu tiếng Việt, xây dựng ứng dụng web Flask gồm 4 phân hệ chính:

- **Phần 1 — Mô phỏng thuật toán Gibbs (`/part1`)**: Tự cài đặt LDA từ đầu bằng **Collapsed Gibbs Sampling** (thuần Python, không dùng thư viện ngoài), chạy demo trên 8 câu tiếng Việt / 2 chủ đề rõ rệt, cho phép tua qua từng vòng lặp.
- **Phần 1' — Tóm tắt dạng "Video" từng bước (`/summarize` hoặc `/simulate`)**: Người dùng nhập **một đoạn văn bản bất kỳ** hoặc chọn **Preset dữ liệu nhỏ 8 câu / Xe điện**, hệ thống mô phỏng toàn bộ hành trình từ đoạn văn tới bản tóm tắt qua **thanh 6 giai đoạn lý thuyết** và **11 cảnh trực quan** dạng video player (hỗ trợ deep link `?preset=toy&scene=6`, scrubber tua vòng lặp Gibbs, phân bố $\theta$ từng câu và top từ khóa theo vòng, công thức với số thực, chấm điểm và chọn câu MMR).
- **Phần 2 — Ứng dụng tóm tắt văn bản trích xuất (`/part2`)**: Ứng dụng LDA (suy luận biến phân qua gensim) để trích xuất các câu đại diện cho văn bản người dùng nhập.
- **Phần 3 — Thử nghiệm & Đánh giá (`/part3`)**: Chạy thử nghiệm trên tập dữ liệu tiếng Việt (offline mẫu hoặc tập `vietnews` từ Hugging Face), so sánh với các baseline Lead-k, Random-k và đánh giá bằng ROUGE-1/2/L cùng Topic Coherence ($u\_mass$).

> 📚 **Tài liệu Bàn giao Kỹ thuật:** Xem chi tiết tại thư mục [`docs/`](docs/):
> - [`docs/part1_mo_ta_tung_buoc.md`](docs/part1_mo_ta_tung_buoc.md): Bảng ánh xạ 6 giai đoạn $\to$ 11 cảnh, ví dụ tính tay 3 token đầu ở vòng 1, các lưu ý trung thực về LL và xác suất $p$.
> - [`docs/part1_kich_ban_demo.md`](docs/part1_kich_ban_demo.md): Kịch bản thuyết trình và demo 6 phút với các URL deep link cụ thể.
> - [`docs/screens/README.md`](docs/screens/README.md): Danh mục các màn hình cần chụp cho slide báo cáo.
> - [`docs/ngoai_pham_vi.md`](docs/ngoai_pham_vi.md): Báo cáo bàn giao các vấn đề tồn đọng ngoài phạm vi tại Phần 2 & 3.

---

## 1. Cài đặt & Khởi chạy

### Yêu cầu môi trường
- Python 3.10+ (đã kiểm thử ổn định trên Python 3.12 và 3.13)
- Trình duyệt hiện đại (hỗ trợ HTML5, SVG, CSS Grid/Flexbox)

### Các bước chạy

```bash
# 1. Tạo và kích hoạt môi trường ảo
python -m venv venv

# Windows (Command Prompt hoặc PowerShell):
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

# 2. Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# 3. Chạy ứng dụng web Flask
python app.py
```

Mở trình duyệt truy cập: **`http://127.0.0.1:5000`**

---

## 2. Cấu trúc thư mục

```
lda_vi_project/
├── app.py                           # Ứng dụng Flask: định tuyến cho cả 4 phân hệ
├── requirements.txt                 # Danh sách gói phụ thuộc (Flask, numpy, gensim, scipy...)
├── README.md                        # Tài liệu hướng dẫn dự án
├── run_experiment.py                # Chạy thử nghiệm Phần 3 từ dòng lệnh
│
├── core/                            # Mã nguồn lõi xử lý thuật toán
│   ├── gibbs_lda.py                 # Collapsed Gibbs Sampling gốc (GIỮ NGUYÊN 100%)
│   ├── trace_lda.py                 # Lớp con TracedGibbsLDA kế thừa GibbsLDA, ghi trace từng token
│   ├── vi_lexicon.py                # Từ điển từ ghép tiếng Việt & stopword (thuần Python)
│   ├── summarizer_preprocess.py     # Tiền xử lý: tách câu an toàn, ghép từ longest-match, ma trận đếm
│   ├── summarizer_pipeline.py       # Pipeline tóm tắt: chấm điểm 0.6cos+0.4p, MMR lambda=0.7
│   ├── sample_text.py               # Đoạn văn bản tiếng Việt mẫu chuẩn
│   ├── toy_data.py                  # Dữ liệu 8 câu demo cho Phần 1
│   ├── lda_pipeline.py              # LDA bằng gensim cho Phần 2 & 3
│   ├── evaluation.py                # Tự cài đặt chỉ số ROUGE-1, ROUGE-2, ROUGE-L
│   ├── dataset_loader.py            # Nạp dữ liệu VietNews hoặc bộ mẫu offline
│   ├── experiment.py                # Pipeline thử nghiệm & so sánh đa phương pháp
│   └── nlp_utils.py                 # Tiện ích NLP dùng chung
│
├── static/                          # Tài nguyên giao diện tĩnh (CSS, JS)
│   ├── css/
│   │   ├── tokens.css               # Hệ thống Design Tokens (màu sắc, typography, spacing)
│   │   └── summarize.css            # Scoped CSS cho Video Player Phần 1' (chuẩn WCAG AAA)
│   ├── js/
│   │   └── summarize-player.js      # Engine Video Player 11 cảnh thuần JS + SVG
│   └── style.css                    # CSS giao diện chung của website
│
├── templates/                       # Giao diện HTML Jinja2
│   ├── base.html                    # Layout khung cơ bản
│   ├── _nav.html                    # Thanh điều hướng thống nhất
│   ├── index.html                   # Trang chủ điều hướng 4 phân hệ
│   ├── part1.html                   # Giao diện Phần 1 (Mô phỏng 8 câu cũ)
│   ├── summarize.html               # Giao diện Phần 1' (Tóm tắt video từng bước)
│   ├── part2.html & part2_result.html # Giao diện Phần 2 (Ứng dụng)
│   └── part3.html & part3_result.html # Giao diện Phần 3 (Thử nghiệm & Đánh giá)
│
├── scripts/                         # Các script hỗ trợ & kiểm thử tự động
│   ├── test_summarizer.py           # Test suite tự động cho Phần 1' (5 tiêu chí a -> e)
│   └── download_stopwords.py        # Tải danh sách stopword mở rộng
│
└── data/                            # Ngữ liệu mẫu và từ điển stopword
    ├── sample_dataset.json          # 10 văn bản mẫu 5 chủ đề
    └── stopwords_vi.txt             # Danh sách từ dừng tiếng Việt
```

---

## 3. Chi tiết Phân hệ 1': Tóm tắt dạng Video Player (`/summarize`)

### 3.1 Nguyên tắc thiết kế & Tự cài đặt
* **Không sửa `core/gibbs_lda.py`:** Demo 8 câu cũ tại `/part1` chạy độc lập, kết quả đồng nhất với cùng seed.
* **Kế thừa sạch trong `core/trace_lda.py`:** Lớp `TracedGibbsLDA` kế thừa `GibbsLDA`, mở rộng phương thức `sweep_with_trace()` để ghi lại từng token (doc $d$, từ $w$, chủ đề cũ $k_{old}$, các số đếm sau rút, xác suất chuẩn hoá/chưa chuẩn hoá, số ngẫu nhiên $r$, chủ đề mới $k_{new}$). Thứ tự và số lần gọi `self.rng.random()` được giữ y hệt giúp kết quả có tính tái lập hoàn toàn.
* **Thuần Python:** Toàn bộ tiền xử lý (tách câu, gộp từ ghép tiếng Việt bằng longest match, lọc stopword) trong `core/summarizer_preprocess.py` và `core/vi_lexicon.py` không dùng bất kỳ thư viện NLP ngoại vi nào (không gensim, underthesea, pyvi, nltk, sklearn).

### 3.2 Hành trình 11 Cảnh của Video Player
1. **Cảnh 1 — Văn bản gốc:** Hiển thị toàn văn đoạn văn bản kèm thẻ thống kê số câu, số từ, độ dài.
2. **Cảnh 2 — Tách câu:** Tách văn bản thành danh sách câu có đánh số thứ tự; bảo vệ số thập phân (`3.5`) và viết tắt (`tp.`, `v.v.`), xử lý ngắt dòng kiểu hard-wrap. Mỗi câu hợp lệ là một document trong LDA.
3. **Cảnh 3 — Tách từ & làm sạch:** Ghép từ ghép tiếng Việt theo nguyên tắc Longest Match dựa trên từ điển (`xe điện`, `môi trường`, `ô nhiễm không khí`...); stopword mờ dần rồi biến mất.
4. **Cảnh 4 — Từ điển & Heatmap câu × từ:** Bảng ma trận tần suất đếm số lần xuất hiện của từng từ nội dung trong từng câu.
5. **Cảnh 5 — Khởi tạo Gibbs:** Gán nhãn chủ đề ngẫu nhiên ban đầu cho tất cả các token; hiển thị bảng $n(d, k)$, bảng $n(k)$ và bảng $n(k, w)$ (từ vựng $\times$ chủ đề).
6. **Cảnh 6 — Gibbs chi tiết vòng 1 (từng từ):** Đi qua từng token, hiển thị công thức suy diễn toán học với **SỐ THỰC**, thanh xác suất có điều kiện, token đổi màu khi gán lại và bộ đếm cập nhật động.
7. **Cảnh 7 — Gibbs tăng tốc (vòng 2..N):** Tích hợp thanh trượt scrubber tua nhanh qua lại giữa các vòng lặp, token đổi màu dần và đồ thị log-likelihood ước lượng minh hoạ xu hướng hội tụ.
8. **Cảnh 8 — Kết quả chủ đề:** Bảng thẻ chủ đề kèm nhãn đặc trưng (top 2–3 từ), xác suất $\phi$ và phân bố $\theta$ của từng câu.
9. **Cảnh 9 — Chấm điểm câu:** Hiển thị công thức chấm điểm kết hợp $\cos(\theta_d, \pi)$ và xác suất sinh từ $\phi$, có hệ số phạt độ dài câu quá ngắn/dài.
10. **Cảnh 10 — Lựa chọn câu bằng MMR:** Thuật toán Maximal Marginal Relevance chọn lọc từng bước ($\lambda = 0.7$), giải thích chi tiết lý do chọn và lý do loại bỏ (trùng ý hoặc điểm thấp).
11. **Cảnh 11 — Bản tóm tắt hoàn chỉnh:** Các câu không được chọn mờ đi, câu được chọn chuyển động mượt mà bay vào khung tóm tắt theo **đúng thứ tự xuất hiện gốc** trong bài; hiển thị thẻ KPI tỉ lệ nén ($3.22\times$, giảm ~69% dung lượng).

### 3.3 Công thức Toán học áp dụng

1. **Lấy mẫu Gibbs có điều kiện (Collapsed Gibbs Sampling):**
   $$P(z_i = k \mid \mathbf{z}_{\neg i}, \mathbf{w}, \alpha, \beta) \propto \frac{n_{d, k}^{\neg i} + \alpha}{\sum_{k'} (n_{d, k'}^{\neg i} + \alpha)} \cdot \frac{n_{k, w}^{\neg i} + \beta}{\sum_{w'} (n_{k, w'}^{\neg i} + \beta)}$$

2. **Phân bố chủ đề toàn đoạn $\pi$:**
   $$\pi_k = \frac{\sum_{d=1}^D n_d \cdot \theta_{d, k}}{\sum_{d=1}^D n_d}$$

3. **Chấm điểm câu:**
   $$\text{Score}(d) = \left[ 0.6 \cdot \cos(\theta_d, \pi) + 0.4 \cdot \frac{1}{|d|} \sum_{w \in d} \left( \sum_{k=1}^K \pi_k \cdot \phi_{k, w} \right) \right] \times \text{LengthFactor}(d)$$

4. **Lựa chọn đa dạng MMR (Maximal Marginal Relevance):**
   $$\text{MMR}(d) = \lambda \cdot \text{Rel}(d) - (1 - \lambda) \cdot \max_{s \in S} \cos(\theta_d, \theta_s) \quad (\lambda = 0.7)$$

---

## 4. Kiểm thử tự động (Test Suite)

Dự án cung cấp bộ kiểm thử tự động toàn diện trong file [`scripts/test_summarizer.py`](scripts/test_summarizer.py). Chạy kiểm thử:

```bash
python scripts/test_summarizer.py
```

### 5 tiêu chí kiểm thử bắt buộc:
* **(a) Demo gốc không đổi:** Mô hình `GibbsLDA` chạy trên 8 câu với `seed=42`, `iterations=20` cho log-likelihood đạt đúng $-162.437$.
* **(b) Tính tương thích lớp con:** `TracedGibbsLDA` và `GibbsLDA` cho cùng trạng thái gán chủ đề và bộ đếm sau vòng 1 và vòng 20 khi cùng seed; thoả mãn bất biến tổng token: $\sum n_{dk} = \sum n_{kw} = \sum n_k = N_{tokens}$.
* **(c) Tính tái lập (Reproducibility):** Cùng seed cho kết quả JSON trung gian giống hệt nhau $100\%$. Khác seed cho kết quả phân bố khác biệt.
* **(d) Độ hội tụ:** Log-likelihood ước lượng tăng dần qua các vòng lặp.
* **(e) Bản tóm tắt chuẩn xác:** Kiểm tra trích xuất đúng 3 câu tiêu biểu của đoạn mẫu (chi phí pin, trạm sạc, và định hướng tương lai), giữ nguyên thứ tự gốc.

---

## 5. Đặc tả API Endpoint

### `POST /api/summarize`
Nhận dữ liệu văn bản và tham số, trả về toàn bộ dữ liệu trung gian của 11 cảnh:

* **Request Header:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "text": "Xe điện đang trở thành xu hướng phát triển mạnh mẽ...",
    "K": 2,
    "iterations": 2,
    "alpha": 0.5,
    "beta": 0.1,
    "seed": 42,
    "n_sentences": 3
  }
  ```
* **Response Body (200 OK):**
  * `params`: Các tham số sử dụng.
  * `sentences`: Danh sách câu gốc và ánh xạ document.
  * `sentence_tokens`: Danh sách token có nhãn (`compound`, `word`, `stopword`).
  * `heatmap`: Ma trận đếm từ vựng $\times$ câu.
  * `initial_counts`: Số đếm ngẫu nhiên ban đầu ($n_{dk}, n_k, n_{kw}$).
  * `traces`: Trace chi tiết từng token ở vòng 1.
  * `history`: Snapshot $\theta, \phi, \text{log-likelihood}$ qua từng vòng.
  * `topics`: Nhãn chủ đề, top từ và phân bố $\pi$ toàn đoạn.
  * `scores`: Điểm thành phần của từng câu.
  * `mmr`: Các bước lựa chọn và lý do loại bỏ câu.
  * `summary`: Danh sách câu được chọn và tỉ lệ nén.
* **Mã lỗi (400 Bad Request):** Trả về thông báo tiếng Việt thân thiện khi văn bản rỗng, ít hơn 5 câu, vượt quá 300 từ, hoặc $K > V$.

---

## 6. Giao diện & Trải nghiệm Người dùng (UI/UX)

* **Thiết kế Academic Interactive Studio (Hướng A):** Nền sáng tinh giản, viền mỏng kỹ thuật, thẻ thông tin rõ ràng, bảng màu chủ đề đạt độ tương phản cao (Teal, Indigo, Amber, Rose).
* **Điều khiển linh hoạt:** Hỗ trợ phím tắt (`Space` phát/tạm dừng, mũi tên `←` `→` lùi/tiến bước, `Shift + ←/→` chuyển cảnh, `Home`/`End` về đầu/cuối), chọn tốc độ phát từ $0.5\times$ đến $2.0\times$.
* **Khả năng tiếp cận:** Hỗ trợ chuẩn `prefers-reduced-motion` cho người nhạy cảm chuyển động, giao diện tương thích responsive hoàn hảo từ màn hình di động $375\text{px}$ đến màn hình lớn.
