# Tiến độ

## Stage 1

Trạng thái: `APPROVED`

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 1.1 | Kiểm kê toàn bộ workspace hiện tại | Hoàn tất |
| 1.2 | Đọc báo cáo Markdown và DOCX hiện có | Hoàn tất |
| 1.3 | Đọc cấu trúc và toàn bộ 34.477 dòng, 90 cột của Excel | Hoàn tất |
| 1.4 | Kiểm tra thiếu, trùng, kiểu dữ liệu, công thức, thời gian, nhóm báo cáo, cardinality và ngoại lệ | Hoàn tất |
| 1.5 | Đối chiếu sơ bộ với nguồn chính thức Việt Nam | Hoàn tất |
| 1.6 | Thiết kế mục tiêu dự báo và rolling validation | Hoàn tất |
| 1.7 | Tạo code audit không comment và artifact JSON | Hoàn tất |
| 1.8 | Tạo tài liệu Stage 1 | Hoàn tất |
| 1.9 | Chạy test cuối stage | Hoàn tất |
| 1.10 | Người dùng duyệt Stage 1 | Hoàn tất |

## Stage 2

Trạng thái: `APPROVED`

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 2.1 | Xác nhận target `VND/m2`, TSTĐ tại ngày hiệu lực và không dùng TSSS | Hoàn tất |
| 2.2 | Khóa data contract và danh sách leakage/PII | Hoàn tất |
| 2.3 | Lọc 7.025 TSTĐ và chuẩn hóa văn bản, nhãn, ngày, số | Hoàn tất |
| 2.4 | Tạo 47 feature không dùng target hoặc TSSS | Hoàn tất |
| 2.5 | Tạo development, rolling folds và test cuối theo thời gian | Hoàn tất |
| 2.6 | Sinh dataset sạch cùng contract, quality report và split manifest | Hoàn tất |
| 2.7 | Chạy test cuối stage | Hoàn tất |
| 2.8 | Xác nhận lợi thế kinh doanh và vị trí khung giá có sẵn tại inference | Hoàn tất |
| 2.9 | Người dùng duyệt Stage 2 | Hoàn tất |

## Stage 3

Trạng thái: `APPROVED`

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 3.1 | Khóa test guard và cài dependency phiên bản cố định | Hoàn tất |
| 3.2 | Benchmark baseline, ba alpha Ridge và CatBoost mặc định | Hoàn tất |
| 3.3 | Điều chỉnh CatBoost theo giới hạn CPU có ghi log | Hoàn tất |
| 3.4 | Tuning CatBoost bằng Optuna trên bốn rolling folds | Hoàn tất |
| 3.5 | Tái đánh giá finalist và chọn model bằng pooled MAE | Hoàn tất |
| 3.6 | Fit Ridge candidate trên toàn bộ 6.025 development | Hoàn tất |
| 3.7 | Phân tích fold, tháng, quận, lợi thế, vị trí, giá, road rarity và asset history | Hoàn tất |
| 3.8 | Ghi tham số, hệ số, runtime, lỗi và model checksum | Hoàn tất |
| 3.9 | Chạy test cuối stage | Hoàn tất |
| 3.10 | Người dùng duyệt Stage 3 | Hoàn tất |

## Stage 4

Trạng thái: `WAITING_FOR_USER_APPROVAL`

| Bước | Nội dung | Trạng thái |
|---|---|---|
| 4.1 | Khóa protocol, metric, ngưỡng chấp nhận và test-guard trước đánh giá | Hoàn tất |
| 4.2 | Xây preprocessing suy luận từ input nghiệp vụ | Hoàn tất |
| 4.3 | Hiệu chỉnh khoảng dự báo chỉ bằng rolling OOF | Hoàn tất |
| 4.4 | Mở test khóa và tính metric cuối | Hoàn tất |
| 4.5 | Phân tích test theo thời gian, vị trí, giá, chất lượng và độ quen thuộc | Hoàn tất |
| 4.6 | Đóng gói model contract, OOD guard và ví dụ suy luận | Hoàn tất |
| 4.7 | Viết model card, monitoring, runbook và báo cáo lỗi | Hoàn tất |
| 4.8 | Chạy test tích hợp cuối | Hoàn tất |
| 4.9 | Người dùng duyệt Stage 4 | Đang chờ |
