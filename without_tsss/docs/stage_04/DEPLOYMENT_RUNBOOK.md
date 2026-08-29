# Runbook suy luận

## Điều kiện trước khi chạy

- Dùng đúng Python và dependency trong `requirements-stage4.txt`.
- Xác minh SHA-256 model khớp deployment manifest.
- Chỉ nhận ngày hiệu lực trong phạm vi package hỗ trợ.
- Input không được chứa target, giá trị định giá, giá trị đề xuất hoặc TSSS.

## Input

Payload là một JSON array. Danh sách trường chính thức nằm trong `artifacts/stage_04/model_package/inference_contract.json`. `Lợi thế kinh doanh` và `Vị trí trong khung giá` là bắt buộc theo xác nhận nghiệp vụ.

Ví dụ sẵn có tại `artifacts/stage_04/model_package/example_input.json`.

## Chạy batch

```powershell
& .venv\Scripts\python.exe scripts\predict_stage4.py artifacts\stage_04\model_package\example_input.json output.json
```

## Output

Mỗi record trả:

- `prediction_vnd_m2`.
- Khoảng 80%, 90% và 95%.
- `status`: `automatic`, `manual_review` hoặc `reject`.
- `flags`: lý do ngoài miền hoặc cần kiểm duyệt.
- `interval_width_ratio`.

Ví dụ output nằm tại `artifacts/stage_04/model_package/example_output.json`.

## Xử lý trạng thái

- `automatic`: có thể chuyển sang bước nghiệp vụ tiếp theo nhưng vẫn phải lưu version và interval.
- `manual_review`: không tự động phê duyệt; chuyên viên kiểm tra và ghi reason code.
- `reject`: không sử dụng prediction làm giá chính thức; yêu cầu cập nhật model hoặc quy trình thẩm định thủ công.

## Bảo mật và audit

Không log thông tin liên hệ, mã kho, mã tài sản nguồn, số báo cáo hoặc địa chỉ chi tiết. Log tối thiểu gồm request ID hệ thống, thời điểm, model version/checksum, status, flags, prediction, interval và kết quả override.

## Hạn chế phát hành hiện tại

Package từ chối ngày sau 31/07/2025. Trước khi triển khai thực tế ở thời điểm hiện tại phải tái huấn luyện với dữ liệu mới; không được nới ngày trong config để bỏ qua guard.
