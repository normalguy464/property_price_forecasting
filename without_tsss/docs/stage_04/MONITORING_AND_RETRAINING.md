# Monitoring và tái huấn luyện

## Monitoring ngay khi dự đoán

Theo dõi hàng ngày và tổng hợp hàng tuần:

- Số request, tỷ lệ validation failure, `automatic`, `manual_review`, `reject`.
- Tỷ lệ category mới theo quận, phường, đường, vị trí và lợi thế kinh doanh.
- Missing rate và tỷ lệ cờ chất lượng.
- PSI cho numeric và category chính so với development baseline.
- P05, median, P95 của prediction và độ rộng interval.
- Latency, lỗi tải model và checksum/version đang phục vụ.

Cảnh báo khi PSI từ 0,20; unseen category rate từ 5%; missing rate tăng tuyệt đối 5 điểm phần trăm; hoặc median prediction thay đổi tương đối 20% so với baseline mà không có giải thích nghiệp vụ.

## Monitoring khi có nhãn

Khi TSTĐ thực tế được phê duyệt, tính theo tháng và rolling ba tháng:

- MAE, WAPE, MdAPE, mean error, within 20% và coverage 90%.
- Tách tài sản mới/tái thẩm định.
- Tách quận, phường, đường common/rare/unseen, VT1–VT4, lợi thế và khoảng giá.
- Theo dõi tỷ lệ chuyên viên override, độ lớn override và reason code.

Cảnh báo đỏ khi rolling MAE vượt 19,05 triệu VND/m², WAPE vượt 18%, within 20% dưới 70%, coverage 90% dưới 85% hoặc một phân khúc đủ 30 mẫu có WAPE vượt 25%.

## Lịch tái huấn luyện

- Tối thiểu hàng tháng khi có batch TSTĐ mới.
- Tái huấn luyện sớm khi có thay đổi địa giới, schema, khung giá, chính sách tín dụng hoặc drift vượt ngưỡng hai kỳ liên tiếp.
- Luôn giữ test gần nhất chưa dùng; không tái sử dụng test Stage 4 để chọn model mới.
- Benchmark lại Ridge và tối đa một CatBoost theo cùng rolling folds cập nhật.
- Phát hành version mới chỉ khi vượt model đang chạy trên cùng backtest và test khóa mới.

## Dữ liệu cần bổ sung

Ưu tiên tăng mẫu cho giá cao, lợi thế `Tốt`, Quận 1, Quận 7, Thành phố Thủ Đức, phường/đường hiếm và VT1. Nếu được phép pháp lý, dùng mã vùng hoặc lưới địa lý đủ thô, đã kiểm duyệt riêng tư; không lưu tọa độ hay địa chỉ chi tiết trong log inference mặc định.

## Rollback

Giữ model package, checksum, config, calibration và contract của ít nhất ba version. Khi alert đỏ hoặc schema lỗi, dừng tự động, chuyển toàn bộ request sang manual review và rollback version gần nhất đã được phê duyệt.
