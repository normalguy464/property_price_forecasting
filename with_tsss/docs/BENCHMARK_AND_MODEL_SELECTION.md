# Benchmark và lựa chọn model

## Rolling benchmark

| Variant | MAE | WAPE | Trong biên 20% |
|---|---:|---:|---:|
| Ridge không TSSS đã đóng băng | 15,88 triệu | 14,91% | 77,35% |
| Ridge TSSS alpha 0,1 | 16,83 triệu | 15,80% | 77,08% |
| Ridge TSSS alpha 1 | 15,80 triệu | 14,83% | 78,64% |
| Ridge TSSS alpha 10 | 16,47 triệu | 15,47% | 78,13% |
| Ridge TSSS alpha 100 | 18,95 triệu | 17,80% | 73,91% |
| Ridge chỉ aggregate TSSS | 16,40 triệu | 15,40% | 77,11% |
| Ridge chỉ comparable TSSS | 15,22 triệu | 14,29% | 79,57% |
| CatBoost TSSS trước tuning | 15,07 triệu | 14,15% | 80,38% |
| CatBoost TSSS sau tuning | 14,83 triệu | 13,93% | 80,71% |

Kết luận quan trọng là thêm nhiều aggregate không tự động làm model tốt hơn. Comparable top-5 mang lại tín hiệu mạnh hơn; CatBoost học được tương tác giữa comparable, địa bàn và đặc điểm vật lý tốt hơn Ridge.

## Mức cải thiện chính

So với Ridge không TSSS, CatBoost tuned giảm rolling MAE 1,04 triệu VND/m², tương đương 6,57%; WAPE giảm 0,98 điểm phần trăm; within 20% tăng 3,36 điểm phần trăm.

MAE nhóm từ 200 triệu VND/m² giảm từ 66,95 xuống 61,98 triệu. VT1 giảm từ 29,10 xuống 26,83 triệu. Nhóm lợi thế `Tốt` không cải thiện: 113,66 lên 114,13 triệu trên chỉ 34 mẫu, nên vẫn bắt buộc kiểm duyệt.

## Model cuối

CatBoost trên log target, 311 iterations, depth 5, learning rate 0,201586, L2 27,967804, random strength 0,280511, bagging temperature 0,260620, border count 128, max CTR complexity 1 và `rsm=0,8`.

Optuna giới hạn sáu trial. Best iterations theo fold là 225, 624, 237 và 386; model full development dùng median 311.
