# Thiết kế bài toán dự báo theo thời gian

## Định nghĩa đề xuất

Tại ngày hiệu lực `t`, dự đoán log đơn giá quyền sử dụng đất của một TSTĐ ở Thành phố Hồ Chí Minh từ thuộc tính tài sản, vị trí phân cấp và thông tin thị trường đã có trước hoặc đúng `t`.

Đây là temporal tabular forecasting. Dataset không theo dõi lặp lại ổn định cùng một bất động sản qua nhiều tháng, nên không phù hợp với ARIMA hoặc Prophet trên từng căn nhà. Chỉ có 17 tháng, cũng quá ngắn để dựa vào mô hình chuỗi thời gian phức tạp.

## Hai chế độ triển khai cần chọn

### Chế độ A: dự báo trước thẩm định

Không dùng các TSSS được chọn riêng trong cùng báo cáo. Mô hình chỉ dùng kho giao dịch/rao bán lịch sử trước ngày `t`. Đây là chế độ kiểm tra năng lực tổng quát hóa khó hơn và sạch hơn.

### Chế độ B: trợ lý chuyên viên thẩm định

Cho phép chuyên viên cung cấp danh sách TSSS trước khi dự đoán TSTĐ. Khi đó các đặc trưng tổng hợp TSSS cùng báo cáo là đầu vào nghiệp vụ hợp lệ, nhưng phải được tính riêng cho báo cáo và toàn bộ báo cáo phải nằm cùng một fold. Không được dùng target TSTĐ hay giá trị định giá cuối cùng.

Stage 2 cần người dùng chọn chế độ. Không được trộn hai chế độ trong cùng metric.

## Pipeline dự kiến

1. Khóa test cuối theo tháng hiệu lực.
2. Trong phần phát triển, tạo rolling folds theo thời gian và group theo báo cáo.
3. Fit mọi quy tắc làm sạch, từ điển nhãn hiếm, thống kê vị trí và outlier trên train của fold.
4. Chuẩn hóa Unicode NFC, khoảng trắng, tên địa giới và đường; bảo tồn bản raw để truy vết.
5. Tách schema TSSS/TSTĐ, sửa trường sai nghĩa và tạo cờ missing theo nghiệp vụ.
6. Tạo feature tài sản: log diện tích, mặt tiền, chiều dài, tỷ lệ hình học, vị trí/hẻm, số mặt tiếp giáp, hình dáng, lợi thế kinh doanh.
7. Tạo feature vị trí phân cấp: quận, phường, đường chuẩn hóa; back-off đường đến phường rồi quận.
8. Tạo feature thời gian: tháng, quý, xu hướng, mùa, tuổi giao dịch, lag giá theo vị trí và macro chỉ khi đã công bố.
9. Huấn luyện trên `log1p(target)` hoặc loss MAE phù hợp; hoàn nguyên dự đoán có kiểm soát.
10. Đánh giá tổng và theo phân khúc; hiệu chỉnh khoảng dự báo; ghi lineage.

## Rolling validation minh họa

Với 17 tháng, cấu hình ban đầu có thể là:

| Fold | Train | Gap | Validation |
|---|---|---|---|
| 1 | 2024-03 đến 2024-08 | Không | 2024-09 đến 2024-10 |
| 2 | 2024-03 đến 2024-10 | Không | 2024-11 đến 2024-12 |
| 3 | 2024-03 đến 2024-12 | Không | 2025-01 đến 2025-02 |
| 4 | 2024-03 đến 2025-02 | Không | 2025-03 đến 2025-04 |
| Test cuối | Khóa sau khi tuning | Không | 2025-05 đến 2025-07 |

Nếu dữ liệu nguồn có độ trễ cập nhật, phải thêm gap một tháng. Các mốc cuối sẽ được chốt ở Stage 2 dựa trên chế độ triển khai và số mẫu TSTĐ từng fold.

Ví dụ: khi dự đoán tháng 11/2024, trung vị giá đường chỉ được tính từ các giao dịch có as-of date trước tháng 11/2024. Một đường chưa đủ năm mẫu sẽ lùi về phường; phường chưa đủ mẫu lùi về quận; quận chưa đủ mẫu lùi về toàn thành phố. Mọi threshold được fit lại trong mỗi fold.

## Đặc trưng vị trí không cần tọa độ chính xác

- Quận, phường cũ, phường mới với mapping có hiệu lực theo thời gian.
- Đường đã chuẩn hóa và nhóm đường hiếm.
- Vị trí trong khung giá, khoảng cách đến đường chính, độ rộng hẻm.
- Trung vị và độ phân tán giá lịch sử theo đường, phường, quận với smoothing và lag.
- Hash có salt cho định danh nội bộ nếu cần join, nhưng hash không biến địa chỉ thành tọa độ và không che được địa chỉ từ điển yếu một cách tuyệt đối.

Nếu pháp lý không cho geocode chính xác, không thực hiện geocoding. Có thể dùng mã vùng phân cấp hoặc ô lưới do data owner cung cấp sau khi đã được phê duyệt và đạt mức ẩn danh tối thiểu. Không gửi địa chỉ sang API bên ngoài ở pipeline mặc định.

## Feature tương tác bắt buộc

`Lợi thế kinh doanh = Tốt` ở Quận 1 không tương đương `Tốt` ở Quận 12. CatBoost có thể học tương tác phi tuyến giữa quận, phường, đường, lợi thế, vị trí và thời gian mà không cần tự đặt trọng số. Không dùng learning curve để tìm trọng số feature; learning curve dùng chẩn đoán bias/variance theo kích thước train.

Các tương tác cần kiểm tra bằng SHAP và metric phân khúc, không chỉnh tay hệ số trừ khi có quy tắc nghiệp vụ cần ràng buộc.

## Mô hình và công cụ giới hạn

### Baseline bắt buộc

Trung vị giá lịch sử phân cấp theo đường → phường → quận → thành phố, có minimum count, smoothing và time lag. Baseline này cho biết boosting thực sự cải thiện bao nhiêu so với định giá vị trí đơn giản.

### Ứng viên chính

`CatBoostRegressor` vì xử lý categorical native, missing và tương tác tốt. Các tham số sẽ tuning có giới hạn: depth, learning_rate, l2_leaf_reg, random_strength, bagging_temperature và iterations qua early stopping.

### Đối chứng tối đa một mô hình

LightGBM nếu cài đặt ổn định và categorical được mã hóa theo fold. Nếu dependency hoặc pipeline encoding làm tăng rủi ro, dùng HistGradientBoosting thay thế. Không benchmark thêm Random Forest, XGBoost, neural network và nhiều biến thể chỉ để tối ưu leaderboard.

### Công cụ

- pandas và openpyxl để đọc nguồn và kiểm tra schema.
- scikit-learn cho metric, transformer và kiểm tra pipeline.
- CatBoost cho mô hình chính.
- Optuna cho tuning có ngân sách cố định trên rolling folds.
- SHAP cho giải thích sau khi model đã được chọn.
- Pandera hoặc kiểm tra schema nội bộ cho data contract nếu dependency được duyệt.

Stage 1 chưa cài các thư viện mô hình và chưa chọn tham số.

## Ngoại lai

- Lỗi chắc chắn: sửa từ nguồn hoặc loại khỏi train với reason code.
- Giá cực trị hợp lệ: giữ, dùng log target hoặc loss robust.
- Cực trị theo thống kê: phát hiện trong từng train fold theo nhóm vị trí và thời gian, không theo IQR toàn thành phố.
- Test: không xóa; chỉ gắn cờ và báo metric riêng.

## Metric

Metric tổng trên test được tính trực tiếp trên toàn bộ dòng test, không lấy trung bình đơn giản MAE của các quận.

- Primary: MAE theo đồng/m² sau khi đơn vị được xác nhận.
- Secondary: RMSE, RMSLE, WAPE, MdAPE.
- Vận hành: tỷ lệ dự đoán nằm trong ±10%, ±20%, ±30% và khoảng dự báo 80%/90%.
- Phân khúc: tháng, quận, phường, đường phổ biến/hiếm, khoảng giá, diện tích, TSSS/TSTĐ và cờ chất lượng.

Metric phân khúc là công cụ phát hiện vùng yếu, quyết định back-off, bổ sung dữ liệu và thiết lập từ chối dự đoán. Nó không thay thế metric tổng.

## Tiêu chí thực tế sơ bộ

Không đặt ngưỡng “đạt” trước khi có baseline và yêu cầu kinh doanh. Mô hình chỉ đủ điều kiện thử nghiệm nếu tốt hơn baseline ổn định trên đa số fold, không sụp ở tháng mới, sai số phân khúc trọng yếu nằm trong biên nghiệp vụ, không leakage, có khoảng bất định và có cơ chế cảnh báo ngoài miền dữ liệu.
