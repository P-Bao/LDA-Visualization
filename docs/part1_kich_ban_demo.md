# Kịch bản Thuyết trình & Demo 6 Phút (Phần 1 & 1+)

> Hướng dẫn chi tiết dành cho người thuyết trình (**Cương**).  
> Sử dụng tính năng **Deep link** để nhảy trực tiếp vào từng cảnh mà không cần thao tác bấm chuột phức tạp trong lúc nói.

---

## 1. Timeline Thuyết trình Chi tiết (Tổng thời lượng: 6 phút)

| Mốc thời gian | URL Deep Link mở trực tiếp | Trọng tâm lời dẫn (Nói gì) | Thao tác trên giao diện | Phương án dự phòng (Nếu gặp sự cố) |
|---|---|---|---|---|
| **0:00 – 0:45**<br>(45s) | `http://127.0.0.1:5000/summarize?preset=toy&scene=1` | *"Chào thầy cô và các bạn. Đây là hệ thống mô phỏng thuật toán Collapsed Gibbs Sampling cho LDA tiếng Việt. Chúng em sử dụng bộ dữ liệu nhỏ gồm 8 câu kiểm chứng thuộc 2 chủ đề rõ rệt: 4 câu thể thao và 4 câu công nghệ."* | Nhấn nút **Space** để tạm dừng nếu đang chạy. Chỉ vào khối KPI (8 câu, 49 token nội dung). | Nếu server chưa khởi động: chạy lệnh `python app.py` trong terminal. |
| **0:45 – 1:30**<br>(45s) | `http://127.0.0.1:5000/summarize?preset=toy&scene=3` | *"Ở bước tiền xử lý, thuật toán Longest Matching nhận diện các từ ghép như 'bóng đá', 'sân vận động', 'lập trình viên'. Các từ dừng như 'là', 'những', 'đã' bị loại bỏ vì xuất hiện tràn lan, không mang tín hiệu phân biệt chủ đề."* | Nhấn phím **$\to$** để chuyển qua 4 bước: Hiện từ ghép $\to$ Mờ stopword $\to$ Ẩn stopword $\to$ Hoàn tất BOW. | Nếu giao diện không phản hồi phím mũi tên: Nhấp chuột vào nút **Bước sau ($\to$)** trên thanh điều khiển. |
| **1:30 – 2:00**<br>(30s) | `http://127.0.0.1:5000/summarize?preset=toy&scene=5` | *"Đây là thời điểm khởi tạo Gibbs: mô hình gán hoàn toàn ngẫu nhiên mỗi từ vào một trong 2 chủ đề (màu Teal và Indigo) và lập ra 3 bảng đếm $n(k)$, $n(d, k)$, $n(k, w)$. Hiện tại chưa có chủ đề nào đúng cả."* | Cuộn nhẹ xem 2 bảng đếm bên phải. | Nếu bảng quá dài: Giữ nguyên khung hình, không cần cuộn hết. |
| **2:00 – 3:00**<br>(60s) | `http://127.0.0.1:5000/summarize?preset=toy&scene=6` | *"Tại Cảnh 6, hệ thống soi chiếu từng token đơn lẻ. Ví dụ ở token thứ 3 là từ 'bóng đá': đầu tiên ta rút token ra khỏi bộ đếm, tính xác suất có điều kiện. Vì các từ xung quanh nghiêng về thể thao, xác suất chọn chủ đề 1 lên tới 99.97%. Token lập tức đổi từ màu tím sang màu xanh!"* | Bấm **Bước trước ($\leftarrow$)** rồi **Bước sau ($\to$)** để khán giả thấy chip đổi màu và nhãn `→ chủ đề 1`. | Mở slide ảnh `docs/screens/p1_c06_cong_thuc.png` nếu muốn chỉ rõ từng số hạng. |
| **3:00 – 4:00**<br>(60s) | `http://127.0.0.1:5000/summarize?preset=toy&scene=7` | *"Từ vòng 2 trở đi, thuật toán tăng tốc. Khi kéo thanh trượt từ vòng 1 tới vòng 30, đường log-likelihood tăng dần và ổn định. Cột bên trái cho thấy phân bố $\theta$ của 4 câu đầu thuần màu xanh, 4 câu sau thuần màu tím. Cột bên phải, top từ khóa thể thao và công nghệ tách biệt hoàn toàn!"* | Dùng chuột **kéo thanh trượt Scrubber** từ vòng 1 sang vòng 30. Quan sát các chip từ mới lọt top nhấp nháy flash. | Nếu kéo thanh trượt bị trễ: Nhấn phím mũi tên hoặc click trực tiếp vào mốc vòng 15, vòng 30. |
| **4:00 – 5:00**<br>(60s) | `http://127.0.0.1:5000/summarize?preset=toy&scene=9` | *"Sau khi có chủ đề, mỗi câu được chấm điểm dựa trên độ tương đồng cosin với chủ đề toàn bài và xác suất từ. Sau đó thuật toán MMR chọn câu có điểm cao nhất ở chủ đề 1 (Câu 1), rồi chọn tiếp câu ở chủ đề 2 (Câu 8) đồng thời phạt các câu trùng lặp ý."* | Nhấp chuột vào Cảnh 10 trên thanh stepper hoặc bấm phím **Shift + $\to$** để chuyển qua cảnh MMR. | Giải thích ngắn gọn về đoạn gạch chéo phạt độ dài nếu có câu hỏi. |
| **5:00 – 6:00**<br>(60s) | `http://127.0.0.1:5000/summarize?preset=toy&scene=11` | *"Bản tóm tắt cuối cùng gồm 2 câu đại diện tiêu biểu nhất, được ghép lại đúng theo thứ tự xuất hiện ban đầu trong văn bản. Tỉ lệ nén đạt hơn 3 lần. Sau đây, bạn Bảo sẽ trình bày Phần 2: ứng dụng LDA với thư viện Gensim trên tập văn bản quy mô lớn."* | Trỏ vào 2 câu được chọn trong khung tóm tắt viền xanh. Chuyển trang sang `/part2`. | Bấm vào menu "P2 Ứng dụng tóm tắt" trên thanh điều hướng đầu trang. |

---

## 2. Các Lưu ý Kỹ thuật & Vận hành Quan trọng

### A. Về Kết nối Mạng Internet
- **Giao diện Player (`/summarize`)**: Hoạt động **hoàn toàn offline $100\%$**, toàn bộ icon, thanh stepper và đồ thị log-likelihood được render bằng SVG/HTML/CSS thuần, không tải bất kỳ file script nào từ CDN bên ngoài.
- **Giao diện Demo cũ (`/part1`) và Phần 2, 3**: Có tải thư viện Plotly từ CDN `cdnjs.cloudflare.com`. Nếu phòng thuyết trình mất mạng, hãy trình chiếu hoàn toàn trên giao diện Player `/summarize`.

### B. Bảng Phím tắt Thuyết trình
- **Phím Space**: Phát hoặc Tạm dừng animation.
- **Phím $\to$ / $\leftarrow$**: Tiến / lùi $1$ bước (token hoặc frame).
- **Phím Shift + $\to$ / Shift + $\leftarrow$**: Chuyển ngay sang cảnh kế tiếp / cảnh trước đó.
- **Thanh Stepper (6 giai đoạn trên cùng)**: Nhấp trực tiếp vào bất kỳ bước nào (ví dụ số 3 "Chạy LDA") để đưa player tới cảnh tương ứng.
- **Tốc độ phát**: Đặt ở mức $0.5\times$ hoặc $1\times$ ở góc phải điều khiển để bài trình bày vừa vặn với lời thuyết minh.

### C. Kế hoạch Dự phòng (Backup Plan)
1. Trường hợp máy tính thuyết trình không cài đặt được môi trường Python: Mở bộ ảnh chụp sẵn chất lượng cao trong thư mục `docs/screens/` để chiếu trên slide PowerPoint.
2. Link rút gọn hữu ích:
   - Mở bản tóm tắt nhanh: `http://127.0.0.1:5000/simulate` (tự động chuyển hướng và nạp 8 câu).
   - Mở thẳng cảnh soi công thức: `http://127.0.0.1:5000/summarize?preset=toy&scene=6`.
