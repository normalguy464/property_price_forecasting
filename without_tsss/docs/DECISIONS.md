# Nhật ký quyết định

## D-001: Dừng ở Stage 1

Quyết định: chỉ thực hiện kiểm toán và thiết kế trong lần chạy này.

Lý do: người dùng yêu cầu cổng duyệt sau mỗi stage.

## D-002: Không sửa file Excel nguồn

Quyết định: `Train_noi.xlsx` là nguồn bất biến; mọi output nằm trong `property_price_forecasting`.

Lý do: bảo toàn lineage và khả năng tái lập.

## D-003: Target tạm thời

Quyết định: dùng tạm cột `Đơn giá quyền sử dụng đất (đ/m2)1` để kiểm toán phân phối, chưa dùng để train.

Lý do: cột này đầy đủ và gần trùng cột đơn giá không hậu tố, nhưng còn mâu thuẫn đơn vị và ba bản ghi khác biệt lớn giữa hai cột.

## D-004: Trục thời gian tạm thời

Quyết định: dùng `Thời điểm hiệu lực` làm as-of date trong thiết kế ban đầu.

Lý do: cột đầy đủ, khớp 100% với tháng/năm dẫn xuất và tồn tại cho cả TSSS lẫn TSTĐ. Quyết định này cần xác nhận nghiệp vụ.

## D-005: Không random split

Quyết định: dùng rolling validation theo tháng, test cuối ở các tháng mới nhất và bảo vệ nhóm `Số báo cáo định giá`.

Lý do: random split cho phép tương lai đi vào train và các dòng cùng hồ sơ có thể nằm ở hai phía.

## D-006: Xử lý ngoại lai

Quyết định: không lọc ngoại lai trước split, không lọc test. Quy tắc được fit trên train của từng fold; lỗi chắc chắn được gắn cờ hoặc loại khỏi train theo quy tắc nghiệp vụ có log.

Lý do: tránh leakage và giữ đánh giá thực tế.

## D-007: Mô hình benchmark giới hạn

Quyết định dự kiến: baseline trung vị phân cấp, CatBoostRegressor, và tối đa một boosting đối chứng.

Lý do: phù hợp dữ liệu categorical nhiều, tránh benchmark dàn trải. Chưa có model hoặc tham số nào được chọn ở Stage 1.

## D-008: Bảo vệ dữ liệu nhạy cảm

Quyết định: loại `Thông tin liên hệ` khỏi mô hình và không xuất giá trị nhạy cảm trong artifact audit.

Lý do: thông tin cá nhân không cần thiết cho định giá và tạo rủi ro pháp lý.

## D-009: Chốt hợp đồng nghiệp vụ

Quyết định: target là đồng/m², đối tượng là TSTĐ và thời điểm dự đoán là `Thời điểm hiệu lực`.

Lý do: người dùng phê duyệt sau Stage 1.

## D-010: Loại toàn bộ TSSS

Quyết định: hiểu yêu cầu theo nghĩa đen; không dùng bất kỳ dòng TSSS nào trong train, feature engineering hoặc inference.

Lý do: hệ thống phải tự động định giá ngay khi nhận thông tin căn nhà. Nếu người dùng chỉ muốn cấm TSSS cùng báo cáo, quyết định này phải được sửa ở cổng duyệt Stage 2.

## D-011: Khóa test thời gian

Quyết định: development từ 03/2024 đến 04/2025; test cuối từ 05/2025 đến 07/2025.

Lý do: test có 1.000 TSTĐ và giữ được bốn rolling folds đủ mẫu trong development.

## D-012: Không loại outlier ở Stage 2

Quyết định: giữ đủ 7.025 TSTĐ; chỉ tạo cờ kiểm tra hình học và target.

Lý do: các cực trị có thể hợp lệ theo vị trí, còn test phải phản ánh dữ liệu thực tế. Không có target hoặc ngày bất hợp lệ buộc phải loại.

## D-013: Không dùng macro và thống kê target lịch sử ở Stage 2

Quyết định: chỉ tạo feature lịch và xu hướng từ ngày hiệu lực; chưa dùng VNI, GDP, CPI, lãi suất, vàng, USD hoặc median target theo vị trí.

Lý do: thiếu nguồn và ngày công bố của macro; thống kê target phải được fit theo từng fold ở Stage 3 để tránh leakage.

## D-014: Mã nhóm chỉ phục vụ đánh giá

Quyết định: mã tài sản và số báo cáo được thay bằng ID nhóm số; không nằm trong feature.

Lý do: 910 tài sản lặp lại. ID nhóm cần cho kiểm tra tài sản mới/tái thẩm định nhưng không được cho mô hình ghi nhớ tài sản.

## D-015: Feature nghiệp vụ có sẵn tại inference

Quyết định: `Lợi thế kinh doanh` và `Vị trí trong khung giá` là hai trường đầu vào được cung cấp khi yêu cầu định giá.

Lý do: người dùng xác nhận sau khi xem kết quả Stage 2. Pipeline không phải tự suy ra hai trường này.

## D-016: Artifact nén phải tái lập

Quyết định: cố định `mtime=0` và mức nén trong gzip khi ghi dataset sạch.

Lý do: checksum không được thay đổi chỉ vì thời điểm chạy. Hai lần sinh liên tiếp đã cho cùng SHA-256.

## D-017: Benchmark giới hạn

Quyết định: chỉ benchmark baseline trung vị phân cấp, Ridge với ba alpha và CatBoost. Không thêm Random Forest, XGBoost, neural network hoặc nhiều biến thể boosting.

Lý do: đủ một baseline nghiệp vụ, một mô hình tuyến tính sparse và một boosting categorical; tránh tối ưu dàn trải trên 7.025 mẫu.

## D-018: Metric chọn model

Quyết định: chọn theo MAE pooled trên 3.334 OOF validation rows từ bốn rolling folds.

Lý do: MAE có đơn vị VND/m², phù hợp yêu cầu kinh doanh và đã được chốt trước khi mở test.

## D-019: Chọn Ridge

Quyết định: model candidate là Ridge `alpha=1`, one-hot `min_frequency=5`, numeric StandardScaler, target `log1p`, solver `lsqr`.

Lý do: MAE 15.877.093 thấp nhất. CatBoost tuned đạt 15.883.865, chênh 6.772 VND/m²; khi gần hòa, Ridge đơn giản, nhanh và dễ vận hành hơn.

## D-020: Không mở test ở Stage 3

Quyết định: mọi artifact benchmark, Optuna, rolling và segment đều ghi `test_rows_used=0`.

Lý do: test chỉ được đánh giá một lần ở Stage 4 sau phê duyệt.

## D-021: CatBoost dùng log target

Quyết định: CatBoost tối ưu RMSE trên `log1p(target)` và Optuna chọn bằng MAE sau hoàn nguyên.

Lý do: loss MAE trực tiếp vượt giới hạn CPU; log target giảm ảnh hưởng cực trị và tăng tốc. Tiêu chí cuối vẫn là MAE VND/m².

## D-022: Ngưỡng nghiệm thu được khóa trước khi mở test

Quyết định: model đạt ngưỡng kỹ thuật khi đồng thời có MAE không quá 19.052.512 VND/m², WAPE không quá 18% và ít nhất 70% dự đoán nằm trong sai số 20%.

Lý do: MAE tối đa bằng 120% MAE rolling OOF; hai ngưỡng còn lại là guardrail thực tế. Đây là ngưỡng kỹ thuật nội bộ, không thay thế mức rủi ro do nghiệp vụ phê duyệt.

## D-023: Khoảng dự báo không dùng test

Quyết định: dùng split conformal trên trị tuyệt đối của residual log từ 3.334 dự đoán rolling OOF để tạo khoảng 80%, 90% và 95%.

Lý do: calibration phải hoàn tất trước test và log residual phù hợp hơn với sai số tăng theo mức giá.

## D-024: Ngoài miền dữ liệu không được tự động chấp nhận

Quyết định: từ chối khi ngày định giá ngoài 01/05/2025–31/07/2025 hoặc quận chưa thấy trong development; chuyển kiểm duyệt thủ công với đường/phường hiếm hoặc mới, numeric tail, cờ chất lượng, lợi thế `Tốt`, giá dự đoán cao hoặc khoảng dự báo rộng.

Lý do: One-Hot Encoding có thể vẫn tạo số dự đoán cho category mới nhưng con số đó không đồng nghĩa với đủ bằng chứng để tự động định giá.

## D-025: Model không được dùng cho thời điểm hiện tại nếu chưa tái huấn luyện

Quyết định: package Stage 4 chỉ hỗ trợ ngày hiệu lực đến 31/07/2025. Dữ liệu mới hơn phải kích hoạt từ chối và yêu cầu model mới.

Lý do: development kết thúc 30/04/2025 và test chỉ chứng minh hiệu năng đến 31/07/2025; suy luận xa hơn là ngoại suy chưa được kiểm chứng.

## D-026: Bổ sung kiểm duyệt phường hiếm sau khi đóng băng prediction

Quyết định: bốn test rows có phường xuất hiện dưới 10 lần trong development được bổ sung cờ `rare_ward`. Prediction và metric nghiệm thu không được tính lại; cả bốn vốn đã ở nhóm kiểm duyệt vì đồng thời có đường hiếm.

Lý do: protocol đã quy định địa bàn hiếm phải được kiểm duyệt nhưng implementation ban đầu chỉ gắn cờ đường hiếm. Thay đổi này làm lý do kiểm duyệt đầy đủ và là sửa policy an toàn, không phải tuning model.

## D-027: Nghiệm thu kỹ thuật nhưng chưa phát hành production hiện tại

Quyết định: Ridge được nghiệm thu trên test lịch sử vì đạt đủ ba guardrail: MAE 17.871.591 VND/m², WAPE 15,72% và 79,90% trong biên 20%. Package không được dùng cho ngày sau 31/07/2025.

Lý do: hiệu năng tổng đạt yêu cầu đã khóa, nhưng tháng 07 suy giảm và dữ liệu đã cũ so với thời điểm hiện tại. Production cần dữ liệu mới, rolling validation mới và test khóa mới.
