# Quyết định

## D-WAPE-001

Không thay đổi hai nhánh đã nghiệm thu. Mọi output nằm trong `wape_optimization`.

## D-WAPE-002

WAPE trên một tập cố định có cùng mẫu số với MAE, nên chọn theo pooled rolling MAE cũng đồng thời tối ưu pooled WAPE.

## D-WAPE-003

Feature lịch sử TSTĐ chỉ dùng nhãn có ngày hiệu lực ít nhất bảy ngày trước observation hiện tại để mô phỏng độ trễ hoàn tất nhãn.

## D-WAPE-004

Chọn mô hình bằng pooled rolling OOF trên 3.334 dòng development. Không dùng test 05–07/2025 để chọn model, trọng số, hệ số hiệu chỉnh hoặc iteration.

## D-WAPE-005

Không loại các dòng khó, giá cao hoặc ngoại lai khỏi validation để làm đẹp WAPE. Mục tiêu 10% áp dụng cho toàn bộ population đã khóa.

## D-WAPE-006

Chọn trung bình đều ba dự đoán: model `with_tsss` đã khóa, residual log theo market anchor và residual raw-MAE theo market anchor. Đây là candidate có rolling MAE/WAPE nhỏ nhất trong tập thử nghiệm giới hạn.

## D-WAPE-007

Số iteration fit toàn development là 311 cho model `with_tsss` đã khóa, 443 cho residual log và 295 cho residual raw. Hai giá trị sau lấy từ kết quả rolling, không lấy từ test.

## D-WAPE-008

Không tuyên bố đạt mục tiêu khi WAPE là 13,11%. Test đã mở chỉ được ghi là reused non-confirmatory và trạng thái package là `experiment_not_production_ready`.
