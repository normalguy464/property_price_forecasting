# Báo cáo chất lượng chọn TSSS

Script `scripts/run_retrieval_quality_report.py` chạy retrieval lịch sử trên toàn bộ TSTĐ và ghi hai artifact:

- `artifacts/retrieval_quality_report.json`: thống kê tổng hợp.
- `artifacts/retrieval_quality_rows.jsonl.gz`: một dòng audit không định danh cho mỗi TSTĐ.

Chạy `python scripts/run_retrieval_quality_report.py --top-k 3` tạo artifact riêng có hậu tố `_k3`; artifact mặc định Top-5 không bị ghi đè.

Report đo coverage, đủ Top-5, fallback địa lý, phân phối Top-1/mean/min score, độ mới, mức khớp trường, duplicate structure và độ phân tán giá. Nó còn backtest hai baseline giá diagnostic: weighted raw unit price và weighted estimated unit price của Top-5.

Các baseline này chỉ dùng `target_price_vnd_m2` sau khi retrieval hoàn tất để đánh giá lịch sử. Target không được dùng để chọn TSSS. Vì vậy MAPE/WAPE theo score band cho biết score cao có thực sự tương quan với comparable có ích hay không.

Không so sánh trực tiếp baseline Top-5 với WAPE ensemble để thay thế model; ensemble vẫn là pipeline dự báo độc lập. Nếu score cao nhưng sai số Top-5 vẫn lớn, cần xem lại trọng số distance, duplicate, yếu tố nghiệp vụ chưa có trong score hoặc chất lượng giá rao bán.
