# Protocol đánh giá cuối

## Trạng thái khóa trước test

Protocol này được ghi trước khi chạy đánh giá khóa. Mô hình, target, feature, preprocessing, calibration và ngưỡng nghiệm thu không được thay đổi sau khi thấy kết quả test.

## Mô hình bị khóa

- Ridge `alpha=1`, solver `lsqr`, target `log1p`.
- One-Hot Encoding với `min_frequency=5` và `handle_unknown=ignore`.
- StandardScaler cho numeric.
- Fit trên 6.025 TSTĐ development đến 30/04/2025.
- SHA-256 model: `a5794878956eb7996103293b6313346b770cbdb9fe0585d6aac73d5d5ca61ca0`.

Không được fit lại model, encoder hoặc scaler bằng test.

## Tập test khóa

- 1.000 TSTĐ.
- Cửa sổ test từ 01/05/2025 đến 31/07/2025; quan sát đầu tiên là 04/05/2025.
- 631 tài sản mới và 369 dòng thuộc tài sản đã thấy trong development.
- Chỉ được dùng một lần cho đánh giá cuối.

## Metric và nghiệm thu

Metric chính là MAE VND/m². Các metric bổ sung gồm RMSE, RMSLE, WAPE, MdAPE, mean error và tỷ lệ trong biên 10%, 20%, 30%.

Model đạt ngưỡng kỹ thuật khi đồng thời:

- MAE không quá 19.052.512 VND/m².
- WAPE không quá 18%.
- Tỷ lệ trong biên 20% không thấp hơn 70%.

Ngưỡng này được xác định từ rolling OOF trước khi mở test và không phải cam kết SLA nghiệp vụ.

## Calibration

Khoảng 80%, 90%, 95% dùng split conformal với absolute log residual từ 3.334 OOF development. Test không tham gia tìm quantile.

## Phân khúc bắt buộc

Kết quả được báo theo tháng, quận, phường, độ phổ biến đường/phường, khoảng giá thật, trạng thái chất lượng dữ liệu, lợi thế kinh doanh, vị trí khung giá, tài sản mới/tái thẩm định và trạng thái xử lý tự động.

## Quy tắc ngoài miền

- Từ chối: quận chưa thấy hoặc ngày hiệu lực ngoài phạm vi đã kiểm chứng.
- Kiểm duyệt thủ công: category địa phương mới/hiếm, numeric tail, cờ chất lượng, lợi thế `Tốt`, giá dự đoán từ 200 triệu VND/m² hoặc khoảng 90% quá rộng.
- Tự động: không có cờ từ chối hoặc kiểm duyệt.
