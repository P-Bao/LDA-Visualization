# Danh mục Ảnh Chụp Màn hình cho Slide Báo cáo (Phần 1 & 1+)

> Hướng dẫn dành cho thành viên thiết kế slide (**Phương**).  
> Bộ ảnh chụp từ giao diện web chạy tại local: `http://127.0.0.1:5000`.  
> Khuyến nghị chụp ở tỷ lệ màn hình chuẩn **Desktop ($1280 \times 800$)** và **Mobile ($375 \times 812$)**.

---

## 1. Danh sách Ảnh Desktop ($1280 \times 800$)

| Tên file ảnh | URL trực tiếp để chụp | Mô tả trạng thái cần chụp | Vị trí sử dụng trên Slide |
|---|---|---|---|
| `p1_c01_goc.png` | `/summarize?preset=toy&scene=1` | Cảnh 1: Hiển thị văn bản gốc 8 câu, các thẻ KPI thống kê số câu, số từ, kích thước từ vựng. | Slide giới thiệu bài toán & bộ dữ liệu kiểm chứng. |
| `p1_c03_ghep_tu.png` | `/summarize?preset=toy&scene=3` | Cảnh 3 (Bước 1): Các từ ghép `bóng đá`, `sân vận động`, `lập trình viên` có viền sáng nổi bật. | Slide giải thích tiền xử lý & từ điển tiếng Việt. |
| `p1_c03_bo_stopword.png` | `/summarize?preset=toy&scene=3` | Cảnh 3 (Bước 3): Các từ dừng bị gạch ngang và mờ đi, chỉ còn lại các token nội dung. | Slide giải thích vì sao cần loại bỏ stopword. |
| `p1_c04_heatmap.png` | `/summarize?preset=toy&scene=4` | Cảnh 4: Bảng từ điển và ma trận câu $\times$ từ (Heatmap Bag-of-Words). | Slide giải thích cấu trúc ma trận đếm $n(d, w)$. |
| `p1_c05_khoi_tao.png` | `/summarize?preset=toy&scene=5` | Cảnh 5: Khởi tạo ngẫu nhiên, các token câu được tô màu hỗn độn kèm 3 bảng đếm $n(k), n(d,k), n(k,w)$. | Slide giải thích điểm khởi phát ngẫu nhiên của Gibbs. |
| `p1_c06_cong_thuc.png` | `/summarize?preset=toy&scene=6` | Cảnh 6 (ở token thứ 3 "bóng đá"): Khối công thức hiển thị chi tiết số hạng và xác suất $99.97\%$ chọn chủ đề 1. | **Slide trọng tâm**: Minh hoạ công thức lấy mẫu có điều kiện của Gibbs. |
| `p1_c07_vong01.png` | `/summarize?preset=toy&scene=7` | Cảnh 7 (kéo thanh trượt về Vòng 1): Phân bố $\theta$ và top từ khóa còn lộn xộn. | Slide so sánh: Trạng thái trước khi hội tụ. |
| `p1_c07_vong30.png` | `/summarize?preset=toy&scene=7` | Cảnh 7 (kéo thanh trượt về Vòng 30): Phân bố $\theta$ tách biệt 2 màu rõ rệt, top từ khóa thể thao và công nghệ định hình. | Slide so sánh: Trạng thái sau khi hội tụ 30 vòng. |
| `p1_c08_chu_de.png` | `/summarize?preset=toy&scene=8` | Cảnh 8: 2 thẻ chủ đề kết quả với các từ đặc trưng và phân bố chủ đề toàn đoạn $\pi$. | Slide phân tích chủ đề trích xuất được. |
| `p1_c09_diem.png` | `/summarize?preset=toy&scene=9` | Cảnh 9: Thanh chia điểm chi tiết gồm phần cosin, phần xác suất $p$, và đoạn gạch chéo phạt độ dài. | Slide công thức chấm điểm độ đại diện của câu. |
| `p1_c10_mmr.png` | `/summarize?preset=toy&scene=10` | Cảnh 10: Từng bước lựa chọn câu của thuật toán MMR và lý do loại bỏ các câu trùng ý. | Slide giải thuật chọn câu MMR chống trùng lặp. |
| `p1_c11_tom_tat.png` | `/summarize?preset=toy&scene=11` | Cảnh 11: Khung tóm tắt viền xanh chứa 2 câu được chọn, kèm các chỉ số nén dữ liệu. | Slide kết luận kết quả tóm tắt cuối cùng. |

---

## 2. Danh sách Ảnh Mobile ($375 \times 812$) Minh hoạ Responsive

| Tên file ảnh | URL trực tiếp để chụp | Mô tả trạng thái cần chụp |
|---|---|---|
| `p1_mobile_stepper.png` | `/summarize?preset=toy&scene=3` | Thanh 6 giai đoạn (stepper) co gọn: các bước trước chỉ hiện số tròn, bước đang chọn hiện cả tên chữ; không bị tràn màn hình. |
| `p1_mobile_c07_grid.png` | `/summarize?preset=toy&scene=7` | Khối 2 cột $\theta$ và Top từ khóa tự động xếp chồng thành 1 cột dọc thanh thoát trên thiết bị di động. |

---

## 3. Cách Thao tác Nhanh Khi Chụp
1. Mở trình duyệt Chrome / Edge, nhấn phím **F12** để mở Developer Tools.
2. Nhấn tổ hợp phím **Ctrl + Shift + M** để bật chế độ giả lập thiết bị (Device Toolbar).
3. Đặt kích thước khung hình là **1280 $\times$ 800** hoặc **375 $\times$ 812**.
4. Dán từng đường link URL ở bảng trên vào thanh địa chỉ, đợi $0.5$ giây cho animation ổn định rồi chụp (sử dụng phím tắt chụp vùng của Windows: **Windows + Shift + S** hoặc lệnh Capture Screenshot của DevTools).
