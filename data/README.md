# Dữ liệu sử dụng trong đồ án

Notebook tổng hợp sử dụng tệp đã được duyệt và tiền xử lý ở Bài 1:

```text
data/accidents_preprocessed.csv
```

Đồ án không chạy lại phần chọn dữ liệu và tiền xử lý dữ liệu thô. Hai tệp `us_accidents_classification.csv` và `us_accidents_association_transactions.csv` chỉ được dùng để đối chiếu schema/quy tắc từ bài tập; kết quả đồ án được tái tạo từ `accidents_preprocessed.csv` để giữ khóa `ID` và ngăn imputation trước khi chia train/test.

Snapshot 80.000 dòng chỉ gồm California (59.903) và Texas (20.097), nên không đại diện cho toàn nước Mỹ. `Severity` biểu thị ảnh hưởng lên luồng giao thông, không phải số người bị thương hoặc tử vong.

Snapshot có 7.236 dòng thiếu `Start_Time`/`Hour_of_Day`. Notebook đồ án giữ trạng thái này là `Unknown`, không gán thành ngày thường. `Distance(mi)` không được dùng làm feature chính vì mô tả phạm vi đường đã bị ảnh hưởng và không phù hợp câu hỏi nhận diện sớm.

Nguồn dữ liệu thô và hướng dẫn tải được mô tả trong README gốc của repository. Dữ liệu thô không được commit lên GitHub; nhóm cần giữ đúng snapshot dùng ở Bài 1 trong vùng lưu trữ chung.
