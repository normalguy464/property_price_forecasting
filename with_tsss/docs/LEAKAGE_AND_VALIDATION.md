# Leakage và validation

## Hai trục thời gian

`market_date` cho biết giao dịch/tin rao xảy ra khi nào. `availability_date` cho biết khi nào record được coi là có mặt trong hệ thống. Cả hai đều phải trước TSTĐ; chỉ kiểm tra market date là chưa đủ.

## Cùng báo cáo

TSSS cùng báo cáo luôn bị loại. Trong artifact cuối, số candidate cùng báo cáo còn lại sau availability guard là 0 vì TSSS trong cùng báo cáo thường có availability bằng ngày TSTĐ. Rule report vẫn được giữ làm defense-in-depth.

## Rolling folds

Giữ bốn expanding folds:

- Train đến 08/2024, validation 09–10/2024.
- Train đến 10/2024, validation 11–12/2024.
- Train đến 12/2024, validation 01–02/2025.
- Train đến 02/2025, validation 03–04/2025.

Feature as-of được tính theo ngày của từng observation, kể cả trong train. Không có aggregate fit một lần trên toàn bộ TSSS rồi gắn ngược về quá khứ.

## Test

Test 05–07/2025 đã được mở khi chọn pipeline không TSSS. Nhánh TSSS không dùng test để chọn feature, model, Optuna hoặc iterations. Kết quả test chỉ là đối chứng mô tả và phải có test thời gian mới sau 07/2025 để xác nhận.

## Unit test

Fixture tự động kiểm tra bốn TSSS: chỉ dòng có market và availability trước target, khác báo cáo được tính; dòng availability cùng ngày, market cùng ngày và cùng báo cáo đều bị loại.
