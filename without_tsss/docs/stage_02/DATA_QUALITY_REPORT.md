# Báo cáo chất lượng dữ liệu Stage 2

## Kết quả đầu ra

| Chỉ tiêu | Giá trị |
|---|---:|
| Dòng nguồn | 34.477 |
| TSTĐ nguồn | 7.025 |
| Dòng đầu ra | 7.025 |
| Cột đầu ra | 57 |
| Feature categorical | 9 |
| Feature numeric | 38 |
| Metadata | 6 |
| Target | 2 |
| Diagnostic | 2 |
| TSSS trong đầu ra | 0 |
| Dòng xóa do ngày/target lỗi | 0 |
| Dòng xóa do outlier | 0 |

SHA-256 của dataset sạch nén: `2b0d4b3db2ba22913e3c007c031f01c9a22a4ee3dca8bf4970969539f019200c`. Hai lần sinh liên tiếp cho cùng checksum.

## Phân phối target TSTĐ

| Thống kê | VND/m² |
|---|---:|
| Min | 17.043.802 |
| Median | 85.338.585 |
| P95 | 251.409.896 |
| P99 | 417.341.120 |
| Max | 1.570.839.412 |

## Missing sau làm sạch

Toàn bộ feature numeric không còn missing hoặc vô hạn. Categorical dùng token rõ ràng:

- `ward_old`: 331 token missing.
- `road_segment`: 1.244 token missing.
- Các categorical còn lại: không missing.

Không nội suy phường hoặc đoạn đường bằng target. Phường mới được giữ riêng và đầy đủ.

## Cờ chất lượng

| Cờ | Số dòng | Cách xử lý |
|---|---:|---|
| Tỷ lệ diện tích/(mặt tiền×chiều dài) dưới 0,5 | 17 | Giữ, kiểm tra hồ sơ nếu sai số lớn |
| Tỷ lệ trên 2 | 183 | Giữ; có thể là thửa không chữ nhật hoặc kích thước đại diện |
| Diện tích ngoài 20–2.000 m² | 5 | Giữ |
| Mặt tiền ngoài 2–30 m | 70 | Giữ |
| Chiều dài ngoài 5–80 m | 29 | Giữ |
| Khoảng cách trên 2.000 m hoặc hẻm rộng trên 60 m | 10 | Giữ |
| Target lệch công thức tổng đất/diện tích trên 1% | 383 | Diagnostic, không làm feature |
| Target trên mốc bảng đất 687,2 triệu | 18 | Diagnostic, không tự coi là sai |

Các khoảng 20–2.000 m², 2–30 m, 5–80 m và điều kiện tiếp cận chỉ là ngưỡng rà soát nghiệp vụ, không phải outlier filter.

## Bảo vệ leakage và dữ liệu nhạy cảm

- Không có raw mã tài sản, mã kho, số báo cáo, địa chỉ chi tiết hoặc thông tin liên hệ.
- Không có cột đơn giá trùng, tổng giá trị, giá đề xuất, giá giao dịch hoặc thống kê nhóm.
- ID nhóm tài sản/báo cáo là số nội bộ và chỉ nằm trong metadata.
- Hai cờ dùng target không nằm trong danh sách feature.

## Hạn chế còn lại

- 1.102 đường trên 7.025 dòng tạo nhóm hiếm; cần xử lý theo fold.
- Hai feature `Lợi thế kinh doanh` và `Vị trí trong khung giá` phụ thuộc chất lượng nhập liệu, nhưng đã được xác nhận có sẵn tại inference.
- Target là giá thẩm định, không phải giá giao dịch.
- Không có TSSS khiến tín hiệu thị trường trực tiếp bị giảm theo quyết định nghiệp vụ.
