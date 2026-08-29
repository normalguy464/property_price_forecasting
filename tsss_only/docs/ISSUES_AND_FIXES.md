# Vấn đề và xử lý

## I-TSSS-ONLY-001: Temporal holdout không có tài sản mới

Tất cả 3.706 dòng test có `Mã tài sản` đã xuất hiện trong development. CatBoost có thể học đặc trưng lặp lại của tài sản/địa bàn, làm MAPE 2,91% lạc quan đối với trường hợp tài sản mới.

Xử lý: giữ kết quả như metric cho định giá lại tài sản đã biết, không tuning thêm và không gọi đây là metric production cho tài sản mới. Cần bổ sung group split theo tài sản để đánh giá cold-start.

## I-TSSS-ONLY-002: Model TSSS-only không transfer sang TSTĐ

External test trên 1.000 TSTĐ 05–07/2025 có MAPE 60,45% và median dự đoán chỉ 33,31 triệu đồng/m² so với 91,20 triệu đồng/m² của target. TSTĐ không hề được dùng cho train/chọn model.

Xử lý: không dùng model TSSS-only để dự đoán TSTĐ. Giữ pipeline TSTĐ/with-TSSS cho TSTĐ và coi TSSS-only là nhánh population riêng.
