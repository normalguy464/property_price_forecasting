# Tiến độ pipeline TSSS

| Bước | Trạng thái |
|---|---|
| Audit schema, ngày và giá TSSS | Hoàn tất |
| Khóa eligibility và leakage guard | Hoàn tất |
| Tạo 86 feature as-of cho 7.025 TSTĐ | Hoàn tất |
| Rolling benchmark và 6 trial Optuna | Hoàn tất |
| Đánh giá phân khúc và test cũ không xác nhận | Hoàn tất |
| Đóng gói inference, interval, monitoring và test | Hoàn tất |
| Thí nghiệm sample-weight theo độ hiếm dải giá | Hoàn tất, không promote vì pooled MAPE/WAPE xấu hơn |
| Comparable V2 và feature xu hướng thị trường | Hoàn tất, không vượt baseline |
| Benchmark loss theo pooled rolling MAPE | Hoàn tất, giữ CatBoost hiện tại |
| Chọn và điều chỉnh ba TSSS, blend với CatBoost | Hoàn tất, có tín hiệu cải thiện; chờ test thời gian độc lập trước khi promote |
# Chức năng truy xuất TSSS tham khảo

- Đã thêm retrieval độc lập để trả 3–5 TSSS theo TSTĐ input.
- Đã áp dụng lọc nghiêm ngặt market date, availability date, cửa sổ 365 ngày và cùng báo cáo trước xếp hạng.
- Đã giới hạn output ở mã tham chiếu nội bộ và thông tin định giá cần thiết, không xuất PII hoặc địa chỉ chi tiết.
- Chưa thay đổi CatBoost, metric hay artifact model. Cần duyệt nghiệp vụ trước khi dùng kết quả comparable để hình thành giá chính thức.
- Đã smoke test với `Train_noi.xlsx`: trả 3 TSSS cùng đường, tuổi 52–133 ngày và rule similarity 85,47–93,98/100 cho input mẫu 15/07/2025.
- Đã chạy toàn bộ 17/17 test `with_tsss` thành công trong 23,548 giây.
- Đã bổ sung tài liệu năm ví dụ truy xuất TSSS ở Tân Bình, Quận 7, Thủ Đức, Bình Tân và Quận 12 để minh hoạ trường hợp candidate tốt, yếu, giá phân tán, gần trùng và thiếu yếu tố nghiệp vụ.
