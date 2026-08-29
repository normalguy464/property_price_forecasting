# Pipeline sử dụng TSSS

TSTĐ là target; TSSS lịch sử được dùng để tạo feature thị trường và comparable theo nguyên tắc as-of.

Model cuối là CatBoost tuned, rolling MAE 14,83 triệu VND/m² trên 3.334 OOF rows. TSSS không bao giờ trở thành target row.

Thứ tự chạy và giải thích đầy đủ nằm tại `../WITH_TSSS_PIPELINE_FLOW.md`.
