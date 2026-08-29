# Property Price Forecasting

Dự án này chuyển bài toán định giá bất động sản từ đánh giá tĩnh sang đánh giá ngoài thời gian. Tại thời điểm dự báo `t`, hệ thống chỉ được dùng dữ liệu đã tồn tại trước hoặc đúng `t` và phải được kiểm tra trên các tháng nằm sau tập huấn luyện.

Stage 1 đã tạo snapshot kiểm toán có thể tái lập cho `Train_noi.xlsx`, rà soát toàn bộ 90 trường, so sánh sơ bộ với bối cảnh thị trường và pháp lý Việt Nam, xác định rò rỉ dữ liệu, thiết kế validation thời gian và lập cổng duyệt. Dataset nguồn không bị sửa.

Kết luận quan trọng nhất là chưa thể huấn luyện an toàn trước khi xác nhận đơn vị đích và thời điểm suy luận. Cột `Loại đơn giá` mâu thuẫn với tên và công thức của cột đích; TSSS và TSTĐ còn sử dụng cùng một số cột với ý nghĩa khác nhau.

## Chạy lại kiểm toán Stage 1

```powershell
& <python> scripts\run_stage1_audit.py
& <python> -m unittest discover -s tests -p "test_*.py" -v
```

Python đã dùng ở Stage 1 là Python 3.12.13 trong runtime của workspace. Hai gói cần thiết được ghi tại `requirements-stage1.txt`.

## Chạy lại pipeline Stage 2

```powershell
& <python> scripts\run_stage2_pipeline.py
& <python> -m unittest discover -s tests -p "test_*.py" -v
```

Đầu ra chính là `artifacts/stage_02/cleaned_tstd.jsonl.gz`. File này chỉ chứa TSTĐ và không chứa raw PII hoặc các cột leakage đã xác định.

## Trạng thái phê duyệt

Stage 1, Stage 2 và Stage 3 đã được duyệt. Stage 4 hoàn tất về kỹ thuật và đang chờ duyệt. Ridge đạt test khóa lịch sử nhưng package từ chối ngày sau 31/07/2025; phải tái huấn luyện bằng dữ liệu mới trước khi dùng production hiện tại.

## Chạy lại Stage 3

```powershell
& ..\.venv\Scripts\python.exe scripts\run_stage3_benchmark.py
& ..\.venv\Scripts\python.exe scripts\run_stage3_tuning.py
& ..\.venv\Scripts\python.exe scripts\run_stage3_finalize.py
& ..\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Study Optuna có khả năng resume từ `artifacts/stage_03/optuna_study.db`. Test cuối không được mở trong các lệnh Stage 3.

## Chạy suy luận Stage 4

Không chạy lại `run_stage4_evaluation.py` vì evaluation manifest đã khóa kết quả test. Chạy ví dụ suy luận bằng:

```powershell
& ..\.venv\Scripts\python.exe scripts\predict_stage4.py artifacts\stage_04\model_package\example_input.json output.json
& ..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Kết quả test khóa và giới hạn sử dụng được mô tả trong `docs/stage_04/FINAL_TEST_RESULTS.md` và `docs/stage_04/MODEL_CARD.md`.
