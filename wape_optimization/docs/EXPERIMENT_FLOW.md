# Luồng thử nghiệm WAPE

## Phạm vi tách biệt

`without_tsss` và `with_tsss` là hai pipeline nguồn đã khóa. Nhánh này chỉ đọc cleaned TSTĐ, split, feature TSSS, OOF và model đã có; mọi model, dự đoán và báo cáo mới được ghi trong `wape_optimization`.

## Luồng xử lý

```text
TSTĐ sạch và split thời gian
        +
feature TSSS quá khứ đã khóa
        +
feature TSTĐ lịch sử as-of mới
        |
rolling fold trên development
        |
direct CatBoost và residual CatBoost
        |
blend OOF, chọn theo pooled MAE/WAPE
        |
fit component trên toàn development
        |
package thử nghiệm và test cũ không xác nhận
```

## Bước 1: Khóa đầu vào

- Target là `target_price_vnd_m2` của TSTĐ.
- Development có 6.025 dòng đến 30/04/2025.
- Rolling OOF có 3.334 dòng thuộc bốn fold thời gian đã định nghĩa từ pipeline gốc.
- Test 1.000 dòng từ 05–07/2025 không tham gia lựa chọn.

## Bước 2: Feature lịch sử TSTĐ

Với mỗi ngày dự báo, chỉ nhãn TSTĐ cũ hơn bảy ngày và không thuộc cùng báo cáo mới được dùng. Thống kê count, median, p25, p75 và tuổi dữ liệu được tính theo đường, phường, quận trong cửa sổ 90, 180 và 365 ngày.

Back-off dùng đường khi đủ 3 mẫu, phường khi đủ 5, quận khi đủ 10, nếu không thì dùng lịch sử toàn cục. Lịch sử cùng tài sản gồm số lần trước, giá gần nhất, tuổi và xu hướng giữa hai lần quá khứ. Tổng cộng có 58 feature mới.

## Bước 3: Anchor và mô hình đơn

Market anchor ưu tiên giá ước tính từ comparable TSSS, sau đó back-off thị trường 365, 180, 90 ngày. History anchor ưu tiên giá trước của chính tài sản rồi back-off TSTĐ.

Các biến thể được đánh giá:

- CatBoost `with_tsss` đã khóa.
- Direct CatBoost dự đoán `log1p(target)` với toàn bộ feature.
- Residual log theo market anchor.
- Residual log theo hybrid market/history anchor.
- Residual raw-MAE theo market anchor, trực tiếp theo VND/m².

## Bước 4: Ensemble và selection

Các trọng số 0,25, 0,50 và 0,75, equal blend ba thành phần, global factor và correction tuần tự được so sánh trên cùng rolling OOF. Vì mẫu số WAPE cố định trên population này, tối thiểu pooled MAE cũng tối thiểu pooled WAPE.

Equal blend của model khóa, residual log market và residual raw-MAE market đạt kết quả tốt nhất. Correction tuần tự không cải thiện nên bị loại.

## Bước 5: Fit và đóng gói

Hai component residual được fit lại trên toàn development với iteration lấy từ rolling. Model `with_tsss` đã khóa được tham chiếu bằng đường dẫn và SHA-256; hai component mới được lưu cục bộ cùng checksum. Trọng số mỗi component là 1/3.

## Bước 6: Khoảng dự báo và đối chứng cũ

Khoảng 80%, 90% và 95% được hiệu chỉnh bằng absolute log residual của selected rolling OOF. Sau khi khóa toàn bộ giải pháp mới chạy một lần trên test cũ. Kết quả này chỉ dùng để kiểm tra hành vi, không phải bằng chứng xác nhận độc lập.
