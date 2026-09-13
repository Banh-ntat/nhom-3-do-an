# Mục 3. Tổng hợp liên kỹ thuật

> Bản kỹ thuật cho báo cáo. Số liệu được sinh từ `phan-tich-tong-hop.ipynb` ngày 11/09/2026; không sửa số liệu bằng tay khi đưa sang báo cáo.

## 3.1. Câu hỏi và phạm vi phân tích

Đồ án kết hợp phân lớp và luật kết hợp để trả lời ba câu hỏi:

1. Trong các sự cố được ghi nhận tại California và Texas, tổ hợp điều kiện nào đi cùng tỷ lệ `Severity` 3-4 cao hơn, và xu hướng có ổn định theo nguồn/bang không?
2. Có thể nhận diện nhóm `Severity` 3-4 từ thông tin ban đầu đến mức nào, và mô hình bỏ sót hoặc cảnh báo nhầm bao nhiêu?
3. Luật và mô hình đồng hướng, bổ sung hay cảnh báo giới hạn của nhau ở những nhóm nào?

`Severity` của US Accidents đo mức ảnh hưởng lên luồng giao thông, không đo thương vong. Vì vậy `is_severe = 1` và item `MucDo_Nang` chỉ là tên kỹ thuật cho nhóm `Severity` 3-4. Mọi kết luận dưới đây giới hạn trong snapshot 80.000 dòng gồm California (59.903) và Texas (20.097).

## 3.2. Thiết kế đánh giá chung

Nguồn duy nhất là `accidents_preprocessed.csv` vì còn khóa `ID`. Tệp classification cũ đã impute trước split và tệp transaction cũ đã bỏ `ID`, nên chúng chỉ được dùng đối chiếu schema, không dùng làm kết quả đồ án.

Nhóm tạo split 80/20 theo `ID`, stratify bốn lớp `Severity`, seed 42. Mọi bước học từ dữ liệu chỉ fit trên train; test dùng cho đánh giá cuối và đối chiếu hai kỹ thuật.

| Split | Số sự kiện | Severity 1 | Severity 2 | Severity 3 | Severity 4 | Severity 3-4 |
|---|---:|---:|---:|---:|---:|---:|
| Train | 64.000 | 416 | 52.267 | 10.751 | 566 | 11.317 (17,6828%) |
| Test | 16.000 | 104 | 13.067 | 2.688 | 141 | 2.829 (17,6813%) |

`Distance(mi)` bị loại vì mô tả chiều dài đoạn đường đã bị ảnh hưởng và không phù hợp với mục tiêu nhận diện sớm. Snapshot có 7.236 dòng thiếu thời gian; các dòng này được giữ là `Unknown`, không gán ngầm thành ngày thường.

## 3.3. Lớp bằng chứng dự báo

Mô hình chính dự báo trực tiếp `is_severe`, cùng biến đích nhị phân với consequent của luật. Dummy, Logistic Regression cân bằng và Decision Tree cân bằng được so sánh; mô hình được chọn bằng average precision qua 5-fold stratified CV trên train. Xác suất của cây được hiệu chỉnh sigmoid cũng chỉ bằng train.

| Mô hình | AP CV | Accuracy | Balanced accuracy | Precision 3-4 | Recall 3-4 | F1 3-4 | F1-macro | AP test | ROC AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Decision Tree balanced | 0,3535 | 0,6648 | 0,6689 | 0,3006 | 0,6752 | 0,4160 | 0,5905 | 0,3668 | 0,7312 |
| Logistic Regression balanced | 0,2723 | 0,5676 | 0,6345 | 0,2526 | 0,7381 | 0,3764 | 0,5228 | 0,2794 | 0,6731 |
| Dummy prior | - | 0,8232 | 0,5000 | 0,0000 | 0,0000 | 0,0000 | 0,4515 | 0,1768 | 0,5000 |

Decision Tree (`max_depth=12`, `min_samples_leaf=100`) được chọn vì AP CV cao nhất. Trên test, mô hình nhận diện đúng 1.910/2.829 mẫu `Severity` 3-4, bỏ sót 919 và tạo 4.444 cảnh báo nhầm. Recall 67,52% đi kèm precision chỉ 30,06%, nên mô hình chưa phù hợp để tự động ra quyết định. Brier score sau calibration là 0,1290.

Phân lớp bốn mức được giữ làm nền kỹ thuật, không dùng làm score chính. Decision Tree bốn lớp đạt F1-macro 0,2558 và balanced accuracy 0,4143; kết quả này cho thấy tách chính xác từng mức vẫn khó hơn bài toán nhóm 1-2/3-4.

## 3.4. Lớp bằng chứng luật kết hợp

Transaction train gồm điều kiện thời gian, thời tiết, ánh sáng và hạ tầng; trạng thái thời gian thiếu được mã hóa `Unknown`. FP-Growth được thử với hai ngưỡng support trước khi khóa luật.

| Min-support | Frequent itemsets | Tổng luật | Luật hướng `MucDo_Nang` | Thời gian |
|---:|---:|---:|---:|---:|
| 1% | 1.242 | 5.298 | 55 | 166,57 giây |
| 3% | 521 | 2.388 | 10 | 116,15 giây |

Ngưỡng 1% được giữ để có đủ ứng viên. Luật cuối phải có consequent `MucDo_Nang`, confidence train tối thiểu 20%, lift train tối thiểu 1,2, antecedent không quá ba item, không chứa `Unknown`, không dư thừa và được chọn hoàn toàn trên train.

## 3.5. Đối chiếu trên cùng test set

Antecedent đã khóa được áp lên test, rồi nối dự báo bằng `ID`. Tỷ lệ quan sát và score model của nhóm thỏa luật được so trực tiếp với nhóm không thỏa luật. Bootstrap 1.000 lần tạo khoảng tin cậy 95% cho chênh lệch.

| Rule | Antecedent | Coverage | Tỷ lệ 3-4 | Nhóm còn lại | Lift | Risk model | Recall trong rule | Quan hệ |
|---|---|---:|---:|---:|---:|---:|---:|---|
| R01 | Junction + Nhiệt độ vừa | 4,14% | 25,83% | 17,33% | 1,461 | 23,05% | 73,68% | Đồng hướng, ổn định theo tầng |
| R02 | Cuối tuần + Nhiều mây | 5,32% | 24,32% | 17,31% | 1,376 | 19,37% | 66,18% | Đồng hướng, ổn định theo tầng |
| R03 | Ban ngày + Cuối tuần + Nhiệt độ vừa | 4,72% | 26,49% | 17,25% | 1,498 | 20,01% | 62,00% | Đồng hướng, ổn định theo tầng |
| R04 | Buổi sáng + Nhiệt độ vừa + Nhiều mây | 4,99% | 24,69% | 17,31% | 1,396 | 22,62% | 77,16% | Đồng hướng mẫu gộp, không ổn định theo tầng |
| R05 | Ban ngày + Junction + Ngày thường | 4,59% | 24,66% | 17,35% | 1,395 | 22,48% | 74,59% | Đồng hướng, ổn định theo tầng |
| R06 | Junction + Ngày thường | 6,78% | 24,79% | 17,16% | 1,402 | 21,87% | 73,98% | Đồng hướng, ổn định theo tầng |
| R07 | Trưa-chiều + Nhiệt độ vừa + Nhiều mây | 4,94% | 23,04% | 17,40% | 1,303 | 21,42% | 73,63% | Đồng hướng, ổn định theo tầng |
| R08 | Ngày thường + Nhiệt độ vừa + Nhiều mây | 12,09% | 24,81% | 16,70% | 1,403 | 22,38% | 78,13% | Đồng hướng mẫu gộp, không ổn định theo tầng |
| R09 | Cuối tuần + Nhiệt độ vừa | 7,09% | 25,49% | 17,09% | 1,441 | 19,94% | 65,05% | Đồng hướng, ổn định theo tầng |
| R10 | Ban ngày + Junction | 5,91% | 24,74% | 17,24% | 1,399 | 21,43% | 72,22% | Đồng hướng, ổn định theo tầng |

Không dùng từ “xác nhận”: rule và model không phải hai nguồn bằng chứng độc lập. “Đồng hướng” chỉ có nghĩa nhóm thỏa rule có cả tỷ lệ quan sát và score model cao hơn nhóm còn lại.

## 3.6. Kiểm tra thiên lệch và độ bền theo tầng

Tỷ lệ `Severity` 3-4 khác rất mạnh theo nguồn: Source1 = 4,36%, Source2 = 35,36%, Source3 = 35,28%. Tỷ lệ tại CA là 16,36% và TX là 21,64%; tỷ lệ cũng giảm mạnh theo năm trong snapshot. Đây có thể phản ánh khác biệt hệ thống thu thập, phạm vi bao phủ hoặc phân bố thời gian, nên kết quả mẫu gộp có nguy cơ gây hiểu lầm.

Với mỗi rule, nhóm kiểm tra các tầng Source/State có ít nhất 100 mẫu ở cả nhóm rule và nhóm đối chứng. Tám rule giữ chênh lệch dương ở mọi tầng đủ mẫu. R04 và R08 đảo chiều quan sát trong Source2:

- R04: 32,12% trong nhóm rule so với 35,68% ở nhóm còn lại của Source2.
- R08: 34,93% trong nhóm rule so với 35,49% ở nhóm còn lại của Source2.

Do đó R04 và R08 không đủ điều kiện làm phát hiện chính dù lift mẫu gộp đều khoảng 1,40. Đây là ví dụ trực tiếp cho thấy kỹ thuật thứ hai và kiểm tra phân tầng không chỉ đặt cạnh luật mà còn làm giảm mức độ khẳng định của kết quả.

## 3.7. Kết luận liên kỹ thuật ở giai đoạn hiện tại

Hai kỹ thuật bổ sung nhau theo ba hướng:

1. Luật cung cấp tổ hợp ngắn và độ phủ; mô hình cung cấp score cùng lỗi ở cấp từng `ID`.
2. Tám luật có bằng chứng đồng hướng trên test và nhất quán trong các tầng Source/State đủ mẫu, tạo ứng viên cho evidence card.
3. R04/R08 cho thấy kết quả gộp có thể che đảo chiều theo nguồn; chúng được giữ làm bằng chứng về giới hạn, không dùng làm khuyến nghị.

Phần này chưa chứng minh nguyên nhân và chưa cho phép khuyến nghị chính sách. Bước tiếp theo phải dùng 919 false negatives và 4.444 false positives làm bằng chứng cho hạn chế, thử Balanced Random Forest trên cùng split/feature/AP CV, rồi mới chốt 3-5 phát hiện cùng khuyến nghị có điều kiện.
