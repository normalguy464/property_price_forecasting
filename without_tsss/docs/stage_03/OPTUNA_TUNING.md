# Tuning CatBoost bằng Optuna

## Thiết kế

- Sampler: TPE, seed ban đầu 42.
- Pruner: MedianPruner sau các trial khởi động.
- Objective: MAE VND/m² trung bình có trọng số theo số dòng validation của bốn rolling folds.
- Train target: `log1p(đơn giá)`.
- Loss: RMSE; eval metric nội bộ: MAE trên log target.
- Dự đoán được hoàn nguyên trước khi tính objective.
- Test rows used: 0.

## Search space cuối

| Tham số | Không gian |
|---|---|
| `depth` | 4–7 |
| `learning_rate` | 0,03–0,20, log scale |
| `l2_leaf_reg` | 1–30, log scale |
| `random_strength` | 0,05–5, log scale |
| `bagging_temperature` | 0–5 |
| `border_count` | 64, 128, 254 |
| `iterations` | Tối đa 700, early stopping 50 |

Các tham số cố định gồm `max_ctr_complexity=1`, `rsm=0.8`, `one_hot_max_size=10`, `bootstrap_type=Bayesian`, bốn CPU threads và seed 42.

## Ngân sách thực tế

Study lưu 14 record:

- 11 complete.
- Hai fail do tiến trình được dừng có chủ đích.
- Một pruned.
- Hai complete bị lặp khi resume cùng seed.
- Khoảng 10 cấu hình hiệu dụng được đánh giá toàn phần hoặc một phần.

Lịch sử đầy đủ được lưu trong `optuna_trials.json` và `optuna_study.db`.

## Trial tốt nhất

| Tham số | Giá trị |
|---|---:|
| Trial | 0 |
| `depth` | 5 |
| `learning_rate` | 0,1821474442 |
| `l2_leaf_reg` | 12,0571262874 |
| `random_strength` | 0,7875660250 |
| `bagging_temperature` | 0,7800932022 |
| `border_count` | 254 |
| Vòng tốt nhất theo fold | 236, 664, 686, 699 |
| Vòng median khuyến nghị | 675 |

MAE theo fold của trial tốt nhất:

- Fold 1: 15,372 triệu.
- Fold 2: 18,245 triệu.
- Fold 3: 13,807 triệu.
- Fold 4: 15,306 triệu.
- Pooled objective: 15,884 triệu VND/m².

## Khó khăn và sửa đổi

Hai cấu hình ban đầu timeout vì MAE trực tiếp và categorical combination. Việc đổi sang log target cùng giới hạn CTR làm benchmark giảm xuống 84,9 giây. Các lần dừng/resume, trial fail và trial lặp đều được giữ trong study để audit, không xóa lịch sử nhằm làm kết quả đẹp hơn.
