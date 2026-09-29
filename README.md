# LDA cho văn bản tiếng Việt — Mô phỏng · Ứng dụng · Thử nghiệm

Dự án web (Flask) chia làm 3 phần theo đúng yêu cầu:

- **Phần 1 — Mô phỏng thuật toán**: cài đặt LDA từ đầu bằng Collapsed Gibbs Sampling (không dùng thư viện có sẵn), chạy trên 8 câu tiếng Việt nhỏ, cho phép tua qua từng vòng lặp để xem thuật toán "học" dần dần.
- **Phần 2 — Ứng dụng**: dùng LDA (bản gensim, cùng thuật toán nhưng suy luận bằng variational inference để chạy nhanh trên dữ liệu thật) để xây hệ thống tóm tắt văn bản trích xuất.
- **Phần 3 — Thử nghiệm**: chạy pipeline ở Phần 2 trên một tập 10 văn bản tiếng Việt (5 chủ đề), đánh giá bằng ROUGE-1/2/L và topic coherence.

## 1. Cài đặt & chạy

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Mở `http://127.0.0.1:5000` — trang chủ có link tới cả 3 phần.

`underthesea` sẽ tự tải một số dữ liệu tách từ tiếng Việt ở lần chạy đầu
(cần internet lần đầu).

## 2. Cấu trúc thư mục

```
lda_vi_project/
├── app.py                     # Flask app: route cho cả 3 phần
├── core/
│   ├── nlp_utils.py            # Tách câu, tách từ tiếng Việt, lọc stopword (dùng chung)
│   ├── gibbs_lda.py             # LDA tự cài đặt (Collapsed Gibbs Sampling) — PHẦN 1
│   ├── toy_data.py              # 8 câu mẫu, 2 chủ đề rõ rệt — dữ liệu cho PHẦN 1
│   ├── lda_pipeline.py          # LDA bằng gensim + tóm tắt trích xuất — PHẦN 2 & 3
│   ├── evaluation.py            # ROUGE-N / ROUGE-L tự cài đặt — PHẦN 3
│   ├── dataset_loader.py        # Nạp dataset: bundled offline hoặc harouzie/vietnews (HF) — PHẦN 3
│   └── experiment.py            # Quy trình thử nghiệm: LDA vs Lead-k vs Random-k + coherence — PHẦN 3
├── data/
│   ├── stopwords_vi.txt
│   └── sample_dataset.json      # 10 văn bản, 5 chủ đề, có tóm tắt tham chiếu
├── templates/                   # Giao diện Flask (Jinja2) cho từng trang
├── scripts/download_stopwords.py  # Tải & gộp stopword tiếng Việt công khai
├── run_experiment.py          # Chạy Phần 3 bằng dòng lệnh, xuất results/*.json, *.csv
├── static/style.css
└── requirements.txt
```

## 3. Phần 1 — Mô phỏng thuật toán chi tiết

File `core/gibbs_lda.py` cài đặt LDA bằng **Collapsed Gibbs Sampling** từ con số 0 (không dùng gensim/sklearn), để mọi trạng thái nội bộ đều lộ ra:

- Mỗi từ trong mỗi câu có một biến ẩn `z` = chủ đề được gán cho từ đó.
- Ở mỗi vòng lặp (sweep), thuật toán lần lượt xét từng từ: **rút** gán chủ đề hiện tại ra khỏi 3 bộ đếm (`n_dk`, `n_kw`, `n_k`), rồi **lấy mẫu lại** chủ đề mới theo công thức xác suất có điều kiện chuẩn của LDA, sau đó **cập nhật** lại bộ đếm.
- Sau mỗi vòng lặp, chương trình chụp lại (snapshot) toàn bộ trạng thái: gán chủ đề của từng từ, ước lượng θ (phân bố văn bản–chủ đề), ước lượng φ (top từ mỗi chủ đề), và một log-likelihood ước lượng để vẽ đường hội tụ.
- Trang `/part1` nạp toàn bộ lịch sử các snapshot này về trình duyệt một lần, rồi dùng thanh trượt (và nút Phát để tự động chạy) để "tua" qua từng bước — người dùng thấy rõ màu chủ đề của từng từ đổi dần và ổn định lại theo đúng 2 chủ đề thể thao / công nghệ sau vài vòng lặp.

## 4. Phần 2 — Ứng dụng tóm tắt trích xuất

File `core/lda_pipeline.py::summarize_extractive()`:

1. Tách văn bản thành câu, tách từ + lọc stopword từng câu.
2. Coi **mỗi câu là một "document"** trong corpus để huấn luyện LDA (gensim) — nhờ vậy suy ra được phân bố chủ đề riêng cho từng câu.
3. Phân bố chủ đề của **toàn văn bản** = suy luận trên BOW gộp của mọi câu.
4. Chấm điểm mỗi câu: `score = topic_dist(câu) · topic_dist(toàn văn bản)` (tích vô hướng hai vector xác suất) — câu càng phản ánh đúng các chủ đề chiếm ưu thế trong văn bản thì điểm càng cao.
5. Chọn `top_k` câu điểm cao nhất, sắp lại theo thứ tự xuất hiện gốc.

Đây chính xác là ứng dụng thực tế của thuật toán vừa mô phỏng ở Phần 1 — chỉ khác là dùng cách suy luận tham số hiệu quả hơn (variational Bayes trong gensim) thay vì Gibbs sampling từng bước một, để xử lý được văn bản dài trong thời gian ngắn.

## 5. Phần 3 — Thử nghiệm & đánh giá

### 5.1 Dữ liệu
Hai nguồn, chọn trên giao diện `/part3` hoặc bằng `--source` ở dòng lệnh:

- **`vietnews`** — bộ công khai `harouzie/vietnews` trên Hugging Face, các cột `guid, title, abstract, article`. Ánh xạ: `article` → nội dung cần tóm tắt, `abstract` → tóm tắt tham chiếu. Loader (`core/dataset_loader.py`) lấy ngẫu nhiên N bài (cố định seed=42 để tái lập), bỏ bài quá ngắn (< 4 câu) hoặc quá dài (> 6000 ký tự), thay dấu `_` bằng khoảng trắng phòng khi văn bản đã tách từ sẵn, và lưu cache vào `data/cache/` để lần sau chạy offline.
- **`sample`** — 10 bài tự viết trong `data/sample_dataset.json`, chạy offline, dùng để thử nhanh.

```bash
pip install datasets
python run_experiment.py --source vietnews --limit 200 --topics 5 --top-k 3
```
Kết quả ghi ra `results/summary.json` (điểm trung bình, coherence) và `results/per_doc.csv` (điểm từng bài, từng phương pháp) để đưa vào báo cáo.

**Stopword:** chạy `python scripts/download_stopwords.py` để tải danh sách công khai (stopwords/vietnamese-stopwords) và gộp vào `data/stopwords_vi.txt`. Từ ghép viết cách bằng khoảng trắng được tự đổi thành `_` khi nạp để khớp đầu ra của underthesea.

### 5.2 Các phép đánh giá

0. **Baseline so sánh:** tóm tắt LDA được so với **Lead-k** (k câu đầu bài, rất
   mạnh với văn bản báo chí) và **Random-k** (k câu ngẫu nhiên). Random-k là mốc
   dưới, Lead-k là mốc trên cần vượt hoặc bàn luận nếu không vượt được. Lưu ý
   `abstract` của Vietnews là tóm tắt tóm lược (abstractive) nên ROUGE của mọi
   phương pháp trích xuất đều ở mức khiêm tốn.

1. **Chất lượng tóm tắt (ROUGE-1 / ROUGE-2 / ROUGE-L)** — so khớp n-gram
   / chuỗi con chung dài nhất giữa bản tóm tắt máy tạo và tóm tắt tham
   chiếu do người viết, cho từng văn bản và trung bình cả tập.
   Cài đặt trong `core/evaluation.py`, không phụ thuộc thư viện ngoài để
   chạy offline; đây là công thức recall/precision/F1 chuẩn nhưng là bản
   **đơn giản hoá**, không phải bản sao chính xác của công cụ ROUGE gốc.
2. **Độ mạch lạc của chủ đề (topic coherence, chỉ số u_mass)** — huấn
   luyện một mô hình LDA riêng ở **cấp độ cả tập văn bản** (mỗi bài báo =
   1 document, khác với Phần 2 là mỗi câu = 1 document), rồi dùng
   `gensim.models.CoherenceModel` để đo mức độ các từ trong cùng 1 chủ đề
   có hay xuất hiện cùng nhau trong corpus hay không. Dùng `u_mass` vì chỉ
   cần chính corpus huấn luyện, không cần thêm dữ liệu tham chiếu ngoài.

### 5.3 Đọc kết quả thế nào
- Bảng ROUGE trung bình + biểu đồ cột F1 theo từng văn bản: đánh giá bản
  tóm tắt máy tạo "giống" tóm tắt người viết đến mức nào.
- Heatmap phân bố chủ đề của từng văn bản: so với cột "Chủ đề gốc" (nhãn
  gán sẵn khi tạo dữ liệu) để xem trực quan LDA có tách đúng nhóm chủ đề
  hay không — đây là một cách đánh giá định tính bổ sung, độc lập với ROUGE.
- Chỉ số coherence: càng gần 0 (ít âm) thì chủ đề càng mạch lạc.

## 6. Hướng mở rộng gợi ý
- Dùng chỉ số coherence (`c_v` thay vì `u_mass`) hoặc quét nhiều giá trị
  `num_topics` để tự động chọn số chủ đề tối ưu thay vì nhập tay.
- Thay công thức chấm điểm câu ở Phần 2 bằng chiến lược "mỗi chủ đề chính
  chọn 1 câu đại diện" để tăng độ đa dạng chủ đề trong bản tóm tắt.
- Mở rộng `stopwords_vi.txt` bằng danh sách stopword tiếng Việt đầy đủ hơn
  từ các bộ dữ liệu NLP công khai để LDA cho kết quả sạch hơn trên văn bản dài.
- Thêm `pyLDAvis` để có bản đồ liên chủ đề (intertopic distance map) tương
  tác đầy đủ ở Phần 3.
