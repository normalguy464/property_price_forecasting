# Suy luận và monitoring

## Input vận hành

Mỗi request cần thông tin TSTĐ và snapshot TSSS warehouse. `Lợi thế kinh doanh` và `Vị trí trong khung giá` vẫn là bắt buộc. Không đưa target, giá trị định giá/đề xuất hoặc TSSS cùng báo cáo vào payload TSTĐ.

```powershell
& ..\.venv\Scripts\python.exe scripts\predict.py artifacts\model_package\example_input.json ..\..\Train_noi.xlsx output.json
```

## Output

Trả point prediction VND/m², conformal interval 80/90/95%, status, flags, count cùng đường, back-off count, comparable count và back-off level. Thiếu TSSS cùng đường/top-5 comparable chuyển `manual_review`; ngày ngoài 01/05–31/07/2025 bị `reject`.

## Production optimization

CLI hiện đọc Excel và tạo feature tại request, phù hợp kiểm chứng nhưng chưa phù hợp latency production. Cần tạo bảng TSSS đã khử PII, index theo availability date/quận/phường/đường, cache rolling aggregate và dịch vụ nearest comparable có version.

## Monitoring

Theo dõi missing/coverage TSSS, tỷ lệ back-off, comparable distance, PSI feature thị trường, prediction distribution, manual-review rate và interval width. Khi có nhãn, báo MAE/WAPE/within 20% theo tháng, quận, coverage, giá và tài sản mới.

Cảnh báo khi PSI từ 0,20; missing rate tăng 5 điểm phần trăm; tỷ lệ thiếu cùng đường/comparable đổi 10 điểm; median prediction đổi 20%; hoặc rolling WAPE vượt 18%.

## Hạn chế

Package dùng availability proxy và dữ liệu đến 31/07/2025. Không được nới supported date trong config để chạy năm 2026; phải bổ sung TSTĐ/TSSS mới, tạo rolling folds mới và test khóa mới.
