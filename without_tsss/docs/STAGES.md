# Kế hoạch theo stage

## Stage 1: Khám phá, kiểm toán và thiết kế

Phạm vi gồm đọc toàn bộ workspace hiện có, lập snapshot dataset, hiểu 90 trường, phát hiện bất hợp lý, kiểm tra sơ bộ theo thị trường Việt Nam, xác định mục tiêu dự báo thời gian, thiết kế pipeline và kiểm thử công cụ audit.

Điều kiện hoàn tất:

- Có profile tái lập và checksum nguồn.
- Có từ điển toàn bộ trường.
- Có danh sách leakage, lỗi chất lượng và câu hỏi nghiệp vụ.
- Có thiết kế split thời gian và danh sách mô hình giới hạn.
- Test Stage 1 đạt.
- Người dùng phê duyệt mới được sang Stage 2.

## Stage 2: Chuẩn hóa, làm sạch và tạo đặc trưng

Chỉ bắt đầu sau phê duyệt Stage 1. Phạm vi dự kiến:

- Chốt target, đối tượng dự đoán và thời điểm suy luận.
- Tách test cuối theo thời gian trước mọi phép fit.
- Chuẩn hóa ngày, địa chỉ phân cấp, Unicode, khoảng trắng và nhãn hiếm.
- Xử lý riêng TSSS/TSTĐ và trường có ý nghĩa khác nhau theo loại kho.
- Tạo cờ lỗi nghiệp vụ; không xóa test và không xóa ngoại lai theo thống kê toàn dữ liệu.
- Xây dựng đặc trưng thời gian, lag và trung vị phân cấp chỉ từ quá khứ.
- Tạo ma trận dữ liệu sạch có lineage.
- Chạy test schema, leakage, thời gian và tính tái lập.

## Stage 3: Benchmark và tuning có kiểm soát

Phạm vi dự kiến:

- Baseline trung vị phân cấp theo quận, phường, đường với back-off.
- CatBoostRegressor là ứng viên chính vì dữ liệu categorical nhiều và cardinality cao.
- Tối đa một mô hình boosting đối chứng nếu dependency và dữ liệu phù hợp.
- Optuna trên rolling validation; ngân sách trial được giới hạn.
- Early stopping theo từng fold.
- Ghi đầy đủ model, tham số, seed, thời gian chạy và metric theo fold/phân khúc.
- Chỉ chốt mô hình sau khi so với baseline và kiểm tra độ ổn định qua thời gian.

## Stage 4: Đánh giá cuối và đóng gói thực tế

Phạm vi dự kiến:

- Khóa pipeline và đánh giá một lần trên test thời gian chưa từng dùng.
- Báo cáo MAE, RMSE, RMSLE, WAPE, MdAPE và tỷ lệ dự đoán trong biên 10%, 20%, 30%.
- Phân tích theo tháng, quận, phường, đường phổ biến/hiếm, khoảng giá, loại kho và chất lượng dữ liệu.
- Hiệu chỉnh khoảng dự báo và cơ chế từ chối dự đoán khi ngoài miền dữ liệu.
- Lập model card, data contract, quy trình monitoring drift và lịch tái huấn luyện.
- Chạy test tích hợp cuối.

## Cổng duyệt

Mỗi stage kết thúc bằng một trạng thái `WAITING_FOR_USER_APPROVAL`. Phê duyệt một stage không tự động phê duyệt thay đổi mục tiêu nghiệp vụ ở stage sau.
