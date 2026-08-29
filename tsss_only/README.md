# TSSS-only pricing pipeline

Nhánh này chỉ dùng dòng TSSS để huấn luyện và dự báo `Đơn giá quyền sử dụng đất (đ/m2)1`. `Tình trạng giao dịch` bị loại hoàn toàn khỏi feature và mọi artifact. Pipeline dùng split thời gian, benchmark baseline/Ridge/CatBoost, sau đó thử log-transform, sample-weight và oversampling chỉ trên train của từng rolling fold.
