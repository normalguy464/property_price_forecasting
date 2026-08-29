# Lựa chọn mô hình Stage 3

## Kết quả finalist

| Metric | Baseline | Ridge | CatBoost tuned |
|---|---:|---:|---:|
| MAE, triệu VND/m² | 30,995 | 15,877 | 15,884 |
| RMSE, triệu VND/m² | 58,677 | 32,262 | 32,987 |
| RMSLE | 0,3564 | 0,1861 | 0,1853 |
| WAPE | 29,10% | 14,91% | 14,91% |
| MdAPE | 18,93% | 9,98% | 9,82% |
| Trong ±10% | 30,71% | 50,03% | 50,66% |
| Trong ±20% | 51,86% | 77,35% | 78,88% |
| Trong ±30% | 67,43% | 91,21% | 90,88% |

## Model được chọn

Ridge được chọn vì có MAE thấp nhất theo quy tắc đã xác định trước. Ridge tốt hơn CatBoost 6.772 VND/m², tương đương khoảng 0,043%. Đây là gần hòa; CatBoost tốt hơn về RMSLE, MdAPE và tỷ lệ trong ±20%, còn Ridge tốt hơn về MAE, RMSE, WAPE và tỷ lệ trong ±30%.

Khi primary metric gần hòa, Ridge có thêm lợi thế:

- Model nhỏ và inference nhanh.
- Pipeline one-hot dễ kiểm toán.
- Không cần runtime CatBoost ở production nếu chỉ triển khai candidate này.
- Ít rủi ro vận hành hơn với 7.025 mẫu.

## Tham số được khóa

```text
model: Ridge
alpha: 1.0
solver: lsqr
max_iter: 5000
tol: 0.0001
categorical encoder: OneHotEncoder
handle_unknown: ignore
min_frequency: 5
numeric transformer: StandardScaler
target transform: log1p
prediction inverse: expm1
random seed: 42
```

Model candidate được fit trên toàn bộ 6.025 development rows và lưu tại `artifacts/stage_03/model/ridge_model.joblib`.

SHA-256: `a5794878956eb7996103293b6313346b770cbdb9fe0585d6aac73d5d5ca61ca0`.

## Trạng thái

Đây chưa phải model production. Nó chưa được đánh giá trên test khóa và chưa có prediction interval, drift monitoring hoặc inference API. Những phần này thuộc Stage 4.
