# Quyết định

## D-TSSS-001

TSTĐ tiếp tục là target. TSSS chỉ tạo feature lịch sử và không được ghép thành observation target.

## D-TSSS-002

Điều kiện thời gian mặc định là ngày TSSS nghiêm ngặt nhỏ hơn ngày hiệu lực TSTĐ do dữ liệu chỉ có độ phân giải ngày.

## D-TSSS-003

`Thời điểm hiệu lực` của dòng TSSS được dùng làm proxy availability. Cả market date và availability date phải nghiêm ngặt trước ngày TSTĐ.

## D-TSSS-004

Dùng riêng `Giá giao dịch/rao bán / diện tích` và `Giá ước tính / diện tích`. Không dùng cột đơn giá đất đã điều chỉnh hoặc `Don_gia_TB`, `Min`, `Max`, độ lệch chuẩn, số lượng mẫu vì lineage tính toán không đủ rõ.

## D-TSSS-005

Feature gồm aggregate 90/180/365 ngày theo đường, phường, quận; back-off theo ngưỡng 5/10/20 mẫu; và top-5 comparable 365 ngày trong cùng quận.

## D-TSSS-006

Chọn model bằng pooled rolling MAE. Chỉ benchmark Ridge và CatBoost; CatBoost tuning giới hạn sáu trial.

## D-TSSS-007

Chọn CatBoost tuned, 311 iterations, depth 5, learning rate 0,201586, L2 27,967804, random strength 0,280511, bagging temperature 0,260620 và border count 128.

## D-TSSS-008

Test 05–07/2025 chỉ là reused non-confirmatory vì đã mở trong pipeline không TSSS. Không được gọi kết quả này là test xác nhận độc lập cho model mới.

## D-TSSS-009

Thí nghiệm xử lý dải giá hiếm dùng sample-weight theo nghịch đảo căn bậc hai của tần suất dải giá, cap 2,0 và chuẩn hóa mean bằng 1. Trọng số chỉ fit từ target train ở từng rolling fold; không oversampling và không dùng test để chọn model.

## D-TSSS-010

Không promote sample-weight cap 2,0: pooled rolling MAPE tăng từ 12,60% lên 12,90% và WAPE tăng từ 13,93% lên 14,28%. Dù nhóm dưới 60 triệu và từ 200 triệu đồng/m² cải thiện MAPE, model chính giữ nguyên để bảo vệ metric toàn bộ danh mục.

## D-TSSS-011

Không promote comparable V2, temporal market hoặc loss mới. Candidate tốt nhất là comparable V2 replacement với MAPE 12,93% và WAPE 14,16%, đều xấu hơn baseline 12,60% và 13,93%. Model CatBoost tuned và 86 feature TSSS hiện tại tiếp tục là model chính.

## D-TSSS-012

Thí nghiệm retrieval–adjustment tạo 208.596 cặp TSTĐ–TSSS as-of, học chọn ba comparable và điều chỉnh giá từng comparable trong giới hạn ±20%. Comparable-only kém CatBoost, nhưng blend cố định 25% retrieval và 75% CatBoost giảm pooled rolling MAE từ 14.834.391 xuống 14.310.600 đồng/m², WAPE từ 13,93% xuống 13,44%, MAPE từ 12,60% xuống 12,24% và tăng `within_10pct` từ 53,51% lên 54,35%.

Không thay model/package hiện tại vì trọng số được chọn trên OOF và test 05–07/2025 đã bị mở. Candidate chỉ chờ test thời gian mới độc lập.
