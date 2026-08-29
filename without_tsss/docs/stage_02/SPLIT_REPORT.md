# Báo cáo chia dữ liệu theo thời gian

## Test cuối

| Tập | Khoảng ngày | Số dòng |
|---|---|---:|
| Development | 01/03/2024–30/04/2025 | 6.025 |
| Test | 04/05/2025–31/07/2025 | 1.000 |

Không có số báo cáo nào xuất hiện ở cả development và test. Có 368 asset group giao nhau, tương ứng 369 dòng test là tài sản từng xuất hiện trong development; 631 dòng test là tài sản mới.

Metric chính Stage 4 sẽ tính trên toàn bộ 1.000 dòng. Stage 3 và 4 phải báo thêm:

- Test tài sản mới: 631 dòng.
- Test tài sản đã từng thẩm định: 369 dòng.

ID tài sản không phải feature nên mô hình không được ghi nhớ bằng mã, nhưng đặc điểm vật lý/vị trí giống nhau vẫn có thể làm nhóm tái thẩm định dễ hơn.

## Rolling folds

| Fold | Train | Số train | Validation | Số validation | Báo cáo giao nhau | Asset group giao nhau |
|---|---|---:|---|---:|---:|---:|
| 1 | 03–08/2024 | 2.691 | 09–10/2024 | 834 | 0 | 59 |
| 2 | 03–10/2024 | 3.525 | 11–12/2024 | 992 | 0 | 62 |
| 3 | 03–12/2024 | 4.517 | 01–02/2025 | 697 | 0 | 61 |
| 4 | 03/2024–02/2025 | 5.214 | 03–04/2025 | 811 | 0 | 211 |

## Quy tắc Stage 3

- Không dùng test để chọn feature, threshold, model hoặc tham số.
- Encoder, nhóm đường hiếm, imputer và thống kê target lịch sử phải fit lại trong train từng fold.
- Early stopping chỉ dùng validation của fold.
- Không lấy validation các tháng trước để làm train trong cùng fold; fold sau được phép mở rộng đến các tháng đã qua.
- Metric rolling được báo theo từng fold và trung bình có trọng số theo số dòng; không che giấu fold xấu bằng một metric duy nhất.

## Asset group

Không ép toàn bộ lần thẩm định của một tài sản vào cùng một phía vì điều đó sẽ phá trật tự thời gian. Thay vào đó giữ time split thực tế và báo riêng tài sản mới/tái thẩm định. Nếu mục tiêu kinh doanh chỉ là căn nhà chưa từng có trong hệ thống, metric tài sản mới phải là metric quyết định.
