# Lỗi và cách xử lý

## I-WAPE-001: Nguy cơ leakage ở xu hướng giá tài sản

Nếu lấy chênh lệch giữa target hiện tại và giá lịch sử làm feature thì target bị rò rỉ trực tiếp. Feature cuối cùng chỉ lấy chênh lệch log giữa hai lần định giá quá khứ đã đủ độ trễ; target hiện tại không tham gia. Test synthetic xác nhận dòng quá gần và dòng cùng báo cáo đều bị loại.

## I-WAPE-002: Sai runtime Python

Lệnh `python` hệ thống trỏ tới Python 3.13 và thiếu `numpy`. Đã chuyển toàn bộ lệnh sang môi trường dùng chung `property_price_forecasting/.venv` có đúng dependency mô hình.

## I-WAPE-003: Sandbox từ chối ghi artifact

Lần fit đầu bằng runtime đúng bị từ chối khi tạo `artifacts/components`. Đã chạy lại cùng script với quyền ghi workspace được phê duyệt; không truy cập mạng và không ghi ra ngoài `wape_optimization`.

## I-WAPE-004: Không có pytest trong môi trường

Không cài thêm dependency. Bộ test dùng `unittest` trong thư viện chuẩn và đạt 10/10.

## I-WAPE-005: Hiệu chỉnh tuần tự không cải thiện

Các correction global, theo dải giá dự đoán và theo dải giá kết hợp vị trí chỉ học từ các fold trước nhưng đều cho WAPE cao hơn equal blend. Chúng được lưu trong `experiment_results.json` để truy vết và không được chọn.

## I-WAPE-006: Mục tiêu 10% chưa đạt

WAPE rolling tốt nhất là 13,11%, còn cao hơn mục tiêu 3,11 điểm phần trăm. Không hạ metric bằng cách lọc validation hoặc dùng test để tuning. Phương án cần dữ liệu mới được ghi trong `LIMITATIONS_AND_NEXT_STEPS.md`.
