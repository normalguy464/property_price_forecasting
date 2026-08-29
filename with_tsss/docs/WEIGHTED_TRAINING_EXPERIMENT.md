# Thí nghiệm sample-weight theo độ hiếm dải giá

## Mục tiêu

Kiểm tra liệu CatBoost có giảm sai số với bất động sản ở dải giá ít quan sát hơn khi tăng trọng số loss cho các dải đó hay không. Đây là thí nghiệm riêng; không thay model đang phát hành và không dùng oversampling.

## Cách làm

Target vẫn là `target_price_vnd_m2` của TSTĐ và model vẫn học `log1p(target)`. Trong mỗi rolling fold, chỉ target của phần train được chia thành bốn dải cố định: dưới 60 triệu, 60–100 triệu, 100–200 triệu và từ 200 triệu đồng/m². Với mỗi dải, trọng số thô là `min(sqrt(n_lớn_nhất / n_dải), 2.0)`, sau đó chuẩn hóa để trung bình trọng số của train bằng 1.

Validation không được weighted, không dùng để tính tần suất dải giá và không được dùng lại để fit. TSSS vẫn chỉ là nguồn tạo feature lịch sử as-of. Vì tần suất được fit riêng trên target train của từng fold, cách này không làm lộ nhãn tương lai.

## Cách đọc kết quả

Artifact `weighted_training_experiment.json` so sánh pooled rolling MAPE, WAPE, MAE và các metric khác với OOF baseline đang phát hành. `weighted_training_oof_predictions.jsonl.gz` chứa prediction theo từng dòng để kiểm tra riêng các dải giá.

Không tự động thay model chính dù metric tốt hơn. Chỉ nên cân nhắc promote sau khi cải thiện ổn định ở rolling OOF và được kiểm tra bằng một tập thời gian mới chưa mở. Nếu metric tổng xấu hơn, giữ model gốc và dùng bảng lỗi theo dải giá để thiết kế feature/comparable chuyên cho nhóm hiếm.

## Kết quả rolling OOF

Trên 3.334 dòng OOF, sample-weight làm MAPE tăng từ 12,60% lên 12,90%, WAPE tăng từ 13,93% lên 14,28% và MAE tăng 369.084 đồng/m². Do đó không promote bản này.

Hai nhóm ít dữ liệu có tín hiệu tốt hơn: nhóm dưới 60 triệu đồng/m² giảm MAPE từ 12,35% xuống 11,70%, nhóm từ 200 triệu đồng/m² giảm từ 18,29% xuống 17,94%. Tuy nhiên hai dải trung tâm đều xấu đi, nên lợi ích cục bộ chưa bù được sai số tổng. Hướng tiếp theo phù hợp là cải thiện feature/comparable cho nhóm giá hiếm hoặc thử trọng số nhẹ hơn; không oversampling trực tiếp các dòng hiếm.
