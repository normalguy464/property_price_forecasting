# Tiến độ

| Bước | Trạng thái | Kết quả |
|---|---|---|
| Khóa nguồn và baseline | Hoàn tất | Hai pipeline nguồn chỉ được đọc |
| Feature TSTĐ lịch sử as-of | Hoàn tất | 58 feature, 7.025 dòng |
| Direct/residual rolling models | Hoàn tất | 5 thành phần chính được đánh giá |
| Ensemble và selection | Hoàn tất | Equal blend đạt WAPE 13,11% |
| Fit toàn development và đóng gói | Hoàn tất | 3 model component có checksum |
| Phân tích phân khúc và khoảng dự báo | Hoàn tất | OOF segment và conformal log-residual |
| Tài liệu và test | Hoàn tất | 12/12 test đạt sau bổ sung retrieval |

## Bổ sung retrieval TSSS

- Đã thêm retrieval 3–5 TSSS as-of cho TSTĐ input, tách hoàn toàn khỏi ensemble WAPE.
- Chưa thay đổi model, metric, artifact prediction hay trạng thái thử nghiệm của nhánh.
- Đã chạy 12/12 test và smoke test CLI với `Train_noi.xlsx`; output thử nghiệm được xoá sau kiểm tra.
- Đã chạy báo cáo toàn bộ 7.025 TSTĐ theo điều kiện lịch sử as-of; artifact ghi nhận coverage 99,79% và estimated Top-5 WAPE 22,53%.
- Đã backtest Top-3: estimated WAPE 22,93%, kém nhẹ Top-5 22,53%; giữ Top-5 làm cấu hình mặc định.

Mục tiêu WAPE dưới 10% chưa đạt. Nhánh đã hoàn tất ở mức thử nghiệm và không được đánh dấu production-ready.
