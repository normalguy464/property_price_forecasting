# Luồng TSSS-only

1. Lọc duy nhất `Phân loại kho = TSSS` và dùng `Thời điểm hiệu lực` làm thời điểm dự báo.
2. Target là `Đơn giá quyền sử dụng đất (đ/m2)1`, không dùng tổng giá trị quyền sử dụng đất làm feature.
3. Bỏ `Tình trạng giao dịch` khỏi contract và feature, do chỉ có 416 trên 27.452 TSSS là đã giao dịch.
4. Chia development/test theo thời gian và đánh giá bằng bốn expanding rolling folds.
5. So sánh hierarchical median, Ridge log, CatBoost log, CatBoost raw, CatBoost sample-weight và CatBoost oversampling.
6. Sample-weight và oversampling chỉ fit trên target của train trong từng fold. Model được chọn theo pooled rolling MAPE, WAPE dùng để phá hòa.
7. Test 05–07/2025 chỉ chạy một lần sau lựa chọn.
