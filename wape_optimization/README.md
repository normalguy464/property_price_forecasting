# WAPE Optimization

Nhánh thử nghiệm độc lập nhằm kiểm tra khả năng đưa WAPE toàn bộ xuống dưới 10%, không sửa artifact của `without_tsss` và `with_tsss`.

Kết quả tốt nhất trên 3.334 dự đoán rolling OOF là WAPE 13,11% và MAE 13,96 triệu VND/m². Kết quả tốt hơn `with_tsss` 5,90% và `without_tsss` 12,08%, nhưng chưa đạt mục tiêu 10%. Trạng thái hiện tại là thí nghiệm, chưa production-ready.

Giải pháp được chọn là trung bình đều của ba thành phần:

- CatBoost `with_tsss` đã khóa.
- CatBoost dự đoán residual log so với market anchor TSSS.
- CatBoost MAE dự đoán residual theo VND/m² so với market anchor TSSS.

Mọi lựa chọn chỉ dựa trên rolling OOF đến 30/04/2025. Test 05–07/2025 đã từng được mở nên chỉ là đối chứng không xác nhận sau khi khóa giải pháp.

## Chạy lại

Từ thư mục này, dùng Python tại `../.venv/Scripts/python.exe` và chạy lần lượt:

```text
scripts/run_history_features.py
scripts/run_experiments.py
scripts/run_additional_experiments.py
scripts/run_finalize.py
```

Chạy test:

```text
../.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Luồng chi tiết nằm trong `docs/EXPERIMENT_FLOW.md`; kết quả và giới hạn nằm trong `docs/RESULTS.md` và `docs/LIMITATIONS_AND_NEXT_STEPS.md`.
