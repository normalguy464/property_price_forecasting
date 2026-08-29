# Hợp đồng nghiệp vụ Stage 2

## Phạm vi đã được duyệt

- Target: đơn giá quyền sử dụng đất, đơn vị `VND/m²`.
- Đối tượng: TSTĐ.
- Thời điểm dự đoán: `Thời điểm hiệu lực`.
- Chế độ: tự động định giá khi nhận thông tin căn nhà.
- TSSS: không sử dụng.

Pipeline hiểu “không sử dụng TSSS” theo nghĩa toàn bộ 27.452 dòng TSSS bị loại trước mọi phép tạo feature. Không có trung vị, giá giao dịch, đường, phường hoặc thống kê nào được học từ TSSS.

## Đầu vào cần có tại inference

| Nhóm | Trường |
|---|---|
| Thời gian | Ngày hiệu lực cần định giá |
| Vị trí | Quận, phường cũ nếu có, phường mới, đường, đoạn đường nếu có |
| Tiếp cận | VT1–VT4, khoảng cách đường chính, độ rộng hẻm |
| Thửa đất | Diện tích, mặt tiền, chiều dài, số mặt tiếp giáp, hình dáng |
| Nghiệp vụ | Mục đích đất, lợi thế kinh doanh, số công trình |
| Yếu tố khác | Các cờ hẻm cụt, đường đâm, công viên, mộ, chùa, quy hoạch, diện tích không công nhận và trục chính |

## Đầu ra

- Dự đoán điểm theo VND/m².
- Khoảng dự báo sẽ được thiết kế ở Stage 4.
- Cờ ngoài miền dữ liệu và lý do từ chối dự đoán sẽ được xác định sau benchmark.

## Ý nghĩa của target

Mô hình sẽ học lại giá thẩm định trong dữ liệu TSTĐ, không phải giá giao dịch thực tế. Vì vậy nó có thể học cả quy tắc và thiên lệch của quy trình thẩm định lịch sử. Metric tốt chỉ chứng minh khả năng tái tạo giá thẩm định ngoài thời gian.

## Điểm cần duyệt trước Stage 3

`Lợi thế kinh doanh` và `Vị trí trong khung giá` đã được xác nhận là có sẵn trong thông tin đầu vào. Pipeline coi đây là hai trường bắt buộc và không tự suy ra.

Test thời gian chứa cả tài sản mới và tài sản tái thẩm định. Đề xuất giữ metric tổng trên đủ 1.000 dòng, đồng thời báo riêng hai phân khúc.
