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
