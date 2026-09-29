# -*- coding: utf-8 -*-
"""
toy_data.py
-----------
Bộ dữ liệu RẤT NHỎ, cố ý chỉ gồm 2 chủ đề rõ ràng (thể thao / công nghệ)
để người dùng dễ dàng quan sát bằng mắt thường việc thuật toán Gibbs
sampling ở Phần 1 hội tụ đúng hướng qua từng vòng lặp.
"""

TOY_SENTENCES = [
    "Đội bóng thi đấu bóng đá rất hay trên sân vận động",
    "Cầu thủ ghi bàn thắng đẹp mắt trong trận đấu bóng đá",
    "Huấn luyện viên của đội bóng khen ngợi tinh thần thi đấu của cầu thủ",
    "Trận đấu bóng đá diễn ra sôi động trên sân vận động",
    "Máy tính mới có cấu hình mạnh giúp lập trình nhanh hơn",
    "Lập trình viên viết phần mềm quản lý dữ liệu khách hàng",
    "Trí tuệ nhân tạo giúp máy tính xử lý dữ liệu chính xác hơn",
    "Công ty công nghệ ra mắt phần mềm lập trình mới",
]

# Ghi chú thiết kế: các câu CÙNG chủ đề cố ý dùng chung nhiều từ khoá cốt lõi
# (vd "bóng_đá", "trận_đấu", "đội_bóng" cho thể thao; "máy_tính", "phần_mềm",
# "lập_trình", "dữ_liệu" cho công nghệ). Đây không phải "mẹo gian lận" mà phản
# ánh đúng bản chất thống kê của LDA: thuật toán suy luận chủ đề dựa trên việc
# từ nào hay xuất hiện CÙNG NHAU giữa các văn bản — vốn từ càng chồng lấp trong
# cùng chủ đề thì mô hình càng dễ hội tụ đúng hướng với ít dữ liệu và ít vòng lặp,
# điều này giúp việc mô phỏng ở Phần 1 dễ quan sát bằng mắt thường hơn.
