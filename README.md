# Property Price Forecasting

Dự án được tách thành hai pipeline chính và một nhánh thử nghiệm độc lập:

- `without_tsss/`: pipeline đã nghiệm thu, chỉ học từ TSTĐ và không dùng TSSS.
- `with_tsss/`: TSTĐ vẫn là target còn TSSS quá khứ hợp lệ được dùng làm bối cảnh thị trường.
- `wape_optimization/`: thử history feature, residual learning và ensemble để kiểm tra mục tiêu WAPE dưới 10%; không sửa hai pipeline chính.

Môi trường Python dùng chung nằm tại `.venv/`.
## Kết quả so sánh rolling

| Pipeline | Model | MAE | WAPE | Trong biên 20% |
|---|---|---:|---:|---:|
| Không TSSS | Ridge | 15,88 triệu VND/m² | 14,91% | 77,35% |
| Có TSSS | CatBoost tuned | 14,83 triệu VND/m² | 13,93% | 80,71% |
| Tối ưu WAPE | Equal blend 3 CatBoost | 13,96 triệu VND/m² | 13,11% | 82,48% |
