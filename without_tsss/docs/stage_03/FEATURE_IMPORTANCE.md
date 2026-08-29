# Giải thích hệ số Ridge

## Cách đọc

Ridge dự đoán log đơn giá. Numeric được StandardScaler và categorical được one-hot, nên hệ số thể hiện thay đổi trên thang log, không phải số VND/m² cộng trực tiếp. Tổng trị tuyệt đối theo feature categorical còn tăng theo số lượng category; vì vậy không được diễn giải `road` lớn gấp bao nhiêu lần `business_advantage` chỉ từ tổng này.

## Feature gốc nổi bật

| Feature | Tổng trị tuyệt đối hệ số | Hệ số mức lớn nhất |
|---|---:|---:|
| `road` | 24,988 | 0,549 |
| `road_segment` | 11,256 | 0,276 |
| `ward_old` | 9,574 | 0,358 |
| `ward_new` | 8,856 | 0,690 |
| `district` | 4,046 | 0,582 |
| `business_advantage` | 0,357 | 0,168 |
| `log_alley_width_m` | 0,260 | 0,260 |
| `price_position` | 0,239 | 0,120 |
| `plot_shape` | 0,168 | 0,063 |
| `land_use` | 0,156 | 0,078 |

Kết quả xác nhận vị trí chi phối mạnh. `Lợi thế kinh doanh` và `Vị trí khung giá` có ảnh hưởng nhưng nhỏ hơn tổng tín hiệu địa lý, đúng với trực giác rằng “Tốt” ở các khu vực khác nhau không đồng giá.

## Ví dụ hệ số one-hot lớn

- Phường An Khánh: hệ số dương khoảng 0,690.
- Quận 1: dương khoảng 0,582.
- Quận 12: âm khoảng -0,470.
- Bình Tân: âm khoảng -0,419.
- Thành phố Thủ Đức: âm khoảng -0,368.

Các hệ số này là hiệu ứng có điều kiện sau khi đã tính các feature còn lại và regularization. Chúng không phải bảng giá độc lập và không nên dùng làm quy tắc nghiệp vụ cứng.

Danh sách đầy đủ 47 feature gốc và 200 one-hot/numeric hệ số lớn nhất nằm trong `artifacts/stage_03/feature_importance.json`.
