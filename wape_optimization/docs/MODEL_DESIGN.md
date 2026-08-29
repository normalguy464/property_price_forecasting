# Thiết kế mô hình

## Feature

Mô hình dùng 200 feature:

- 9 categorical: quận, phường cũ/mới, đường, đoạn đường, vị trí khung giá, mục đích sử dụng đất, hình dạng và lợi thế kinh doanh.
- 38 numeric/quality/time từ pipeline TSTĐ sạch.
- 86 feature thị trường TSSS as-of.
- 58 feature lịch sử TSTĐ as-of.
- 9 anchor và chỉ báo thiếu anchor.

CatBoost xử lý categorical trực tiếp. Không gán trọng số thủ công cho `Lợi thế kinh doanh` hay `Vị trí trong khung giá`; tác động của chúng được học có điều kiện cùng quận/phường/đường và các feature thị trường.

## Ba component cuối

| Component | Nhãn học | Loss | Iteration |
|---|---|---|---:|
| `with_tsss_frozen` | `log1p(target)` | RMSE, đánh giá MAE | 311 |
| `residual_market_log` | `log1p(target) - log1p(market_anchor)` | RMSE, đánh giá MAE | 443 |
| `residual_market_raw` | `target - market_anchor` | MAE | 295 |

Dự đoán cuối bằng trung bình số học với trọng số 1/3 cho mỗi component.

## Tham số residual log

| Tham số | Giá trị |
|---|---:|
| depth | 5 |
| learning_rate | 0,12 |
| l2_leaf_reg | 20 |
| random_strength | 0,3 |
| bagging_temperature | 0,3 |
| border_count | 128 |
| max_ctr_complexity | 1 |
| rsm | 0,8 |
| bootstrap_type | Bayesian |

Residual raw giữ cấu hình trên nhưng learning rate 0,08 và loss MAE. Iteration của các fold residual raw là 292, 298, 300 và 203; median làm tròn dùng cho fit cuối là 295.

## Lý do dùng residual

TSSS cung cấp mặt bằng giá thị trường địa phương. Residual model không phải học lại toàn bộ mức giá từ đầu mà học phần chênh của TSTĐ so với anchor. Bản log ổn định sai số tỷ lệ; bản raw-MAE bám sát đúng hàm mất mát tương ứng với WAPE trên tập cố định. Hai sai số không hoàn toàn giống nhau nên blend giảm MAE tổng.
