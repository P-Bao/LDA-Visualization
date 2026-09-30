# Báo cáo Bàn giao Kỹ thuật & Các Vấn đề Tồn đọng Ngoài Phạm vi (Phần 2 & 3)

> Tài liệu bàn giao kỹ thuật dành cho thành viên phụ trách Phần 2 & Phần 3 (**Bảo**).  
> Theo điều lệ dự án, nhóm thực hiện Phần 1 tuyệt đối tuân thủ phạm vi công việc, không chỉnh sửa trực tiếp vào mã nguồn của Phần 2 & 3. Dưới đây là các phát hiện lỗi kỹ thuật và đề xuất giải pháp tối ưu được ghi nhận trong quá trình rà soát hệ thống.

---

## 1. Danh sách Vấn đề Phát hiện tại Phần 2 & Phần 3

### Vấn đề 1: Ép kiểu số nguyên từ `request.form` không có try-catch (Lỗi HTTP 500)
- **Vị trí**:
  - `app.py`, hàm `part2_analyze()`: dòng ép kiểu `int(request.form.get("num_sentences", 3))`, `int(request.form.get("num_topics", 3))`.
  - `app.py`, hàm `part3_run()`: dòng ép kiểu các tham số form tương tự.
- **Hiện tượng**: Khi người dùng nhập giá trị rỗng, ký tự chữ hoặc tham số ngoài dải hợp lệ, Flask ném ngoại lệ `ValueError` dẫn tới lỗi máy chủ **HTTP 500 Internal Server Error**.
- **Giải pháp khuyến nghị cho Bảo**:
  Tái sử dụng hàm helper `_int_arg(name, default, lo, hi)` tương tự như cách Phần 1 đã cài đặt ở BE-6 để chống crash khi người dùng nhập dữ liệu không hợp lệ:
  ```python
  def _int_form(form, name, default, lo, hi):
      try:
          val = int(form.get(name, default))
          return max(lo, min(hi, val))
      except (ValueError, TypeError):
          return default
  ```

---

### Vấn đề 2: Thuật toán lọc tài liệu bị suy biến độ phức tạp $O(n^2)$ trong `core/experiment.py`
- **Vị trí**: `core/experiment.py`, hàm `run_experiment()`.
- **Đoạn mã hiện tại**:
  ```python
  documents = [d for d in all_docs if d["id"] in {r["id"] for r in per_doc}]
  ```
- **Hiện tượng**: Trong mỗi vòng lặp duyệt tài liệu, tập `set` các id `{r["id"] for r in per_doc}` bị khởi tạo lại liên tục từ đầu. Khi tập dữ liệu tăng lên hàng nghìn bài báo (ví dụ tập Vietnews đầy đủ), độ phức tạp thời gian tăng vọt lên $O(n^2)$, làm trang web bị treo/timeout.
- **Giải pháp khuyến nghị cho Bảo**:
  Khởi tạo tập `valid_ids = {r["id"] for r in per_doc}` **trước vòng lặp một lần duy nhất** để giữ độ phức tạp tra cứu ở mức $O(1)$:
  ```python
  valid_ids = {r["id"] for r in per_doc}
  documents = [d for d in all_docs if d["id"] in valid_ids]
  ```

---

### Vấn đề 3: Không đồng bộ danh sách Từ dừng (Stopwords) và Cơ chế Tách từ
- **Hiện trạng**:
  - **Phần 1 & 1+**: Tách từ thuần Python bằng từ điển Longest Matching (`core/vi_lexicon.py`) kết hợp danh sách từ dừng chọn lọc (đã loại bỏ các từ phá vỡ ngữ nghĩa như `thể`, `thế` ở BE-2).
  - **Phần 2 & 3**: Sử dụng thư viện `underthesea` và nạp từ dừng từ file văn bản thô `stopwords_vi.txt`.
- **Hệ quả**: Một số từ ghép tiếng Việt (ví dụ `thể thao`, `cơ thể`) có thể bị `stopwords_vi.txt` của Phần 2 cắt vụn hoặc bỏ sót.
- **Giải pháp khuyến nghị cho Bảo**:
  Cập nhật file `stopwords_vi.txt` đồng bộ với các cải tiến của `core/vi_lexicon.py` (loại bỏ các từ chức năng đa nghĩa) để cải thiện độ đo Coherence và ROUGE của Phần 3.

---

### Vấn đề 4: Phụ thuộc vào CDN Plotly khi chạy Offline
- **Hiện trạng**: `templates/part1.html`, `templates/part2.html` và `templates/part3.html` đều nạp script Plotly từ URL CDN: `https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.32.0/plotly.min.js`.
- **Hệ quả**: Nếu môi trường báo cáo / chấm bài không có kết nối Internet, các biểu đồ phân bố và ma trận của Phần 2 & 3 sẽ không thể hiển thị.
- **Giải pháp khuyến nghị cho Bảo**:
  Tải file `plotly.min.js` về lưu cục bộ tại `static/js/vendor/plotly.min.js` và chuyển đường dẫn `script` sang nạp nội bộ tương tự như giao diện Player của Phần 1+.
