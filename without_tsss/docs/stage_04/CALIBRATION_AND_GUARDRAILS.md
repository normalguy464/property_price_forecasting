# Khoảng dự báo và guardrail

## Calibration

Khoảng dự báo dùng split conformal trên absolute residual trong không gian `log1p`. Nguồn calibration là 3.334 rolling OOF rows, không phải train prediction và không chứa test.

| Khoảng danh nghĩa | Coverage test | Độ rộng trung bình |
|---|---:|---:|
| 80% | 82,70% | 46,37 triệu VND/m² |
| 90% | 91,60% | 64,94 triệu VND/m² |
| 95% | 95,30% | 84,17 triệu VND/m² |

Coverage tổng đạt hoặc cao hơn danh nghĩa. Khoảng 90% vẫn rất rộng, phản ánh đúng độ bất định còn lớn của bài toán chứ không phải sai số điểm đã được giải quyết.

Coverage 90% theo tháng là 92,67% ở tháng 5, 94,98% ở tháng 6 và 87,92% ở tháng 7. Sự giảm coverage tháng 7 là thêm một dấu hiệu drift theo thời gian.

## Trạng thái suy luận

`automatic` chỉ được trả về khi không có cờ ngoài miền. `manual_review` vẫn trả prediction và khoảng dự báo nhưng chuyên viên phải kiểm tra. `reject` có nghĩa model hiện tại không đủ bằng chứng để đưa ra kết quả vận hành.

## Điều kiện từ chối

- Ngày hiệu lực trước 01/05/2025 hoặc sau 31/07/2025.
- Quận chưa từng xuất hiện trong 6.025 development rows.
- Thiếu trường bắt buộc, numeric không hữu hạn hoặc kích thước vật lý không hợp lệ sẽ phát sinh lỗi validation thay vì dự đoán.

## Điều kiện kiểm duyệt thủ công

- Đường chưa thấy hoặc xuất hiện dưới 5 lần.
- Phường chưa thấy hoặc xuất hiện dưới 10 lần.
- Numeric nằm ngoài khoảng quantile 0,5%–99,5% của development.
- Có cờ hình học, diện tích, mặt tiền, chiều dài hoặc khả năng tiếp cận.
- `Lợi thế kinh doanh = Tốt`.
- Giá dự đoán từ 200 triệu VND/m².
- Độ rộng khoảng 90% lớn hơn 75% point prediction.

## Diễn giải đúng

Khoảng conformal là coverage thực nghiệm theo quần thể, không phải xác suất chắc chắn cho riêng một căn nhà. Khi distribution drift hoặc group quá hiếm, coverage có thể giảm; do đó interval không thay thế human review.
