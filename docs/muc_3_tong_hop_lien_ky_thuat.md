# 3. Tổng hợp liên kỹ thuật

> Bản nội dung kỹ thuật để đưa vào báo cáo. Các số liệu được sinh từ `phan-tich-tong-hop.ipynb`; không thay đổi số liệu bằng cách nhập tay.

## 3.1. Kết hợp các kỹ thuật quanh câu hỏi dẫn dắt

Đồ án kết hợp **luật kết hợp**, **mô hình phân lớp** và **thống kê kiểm định độ bền** trên cùng một tập gồm 16.000 sự cố test. Mỗi dòng được nối bằng `ID`; do đó kết quả các kỹ thuật cùng mô tả đúng một nhóm sự cố, thay vì chỉ được đặt cạnh nhau.

`Severity` trong bộ dữ liệu biểu thị mức ảnh hưởng của sự cố lên luồng giao thông, không biểu thị thương vong. Nhãn chung của phần tổng hợp là `is_severe = 1` khi `Severity` thuộc 3-4. Mọi kết luận chỉ áp dụng cho snapshot 80.000 sự cố gồm California và Texas.

### 3.1.1. Thiết kế kết hợp và kiểm soát đánh giá

Nhóm tạo một split 80/20 duy nhất, stratify theo bốn lớp `Severity` và cố định `random_state=42`. Tập train có 64.000 sự cố; tập test có 16.000 sự cố. Tỷ lệ Severity 3-4 gần như không đổi giữa train (17,6828%) và test (17,6813%).

Mọi thao tác học từ dữ liệu, gồm imputation, scaling, calibration, lựa chọn mô hình, khai phá và chọn luật, chỉ sử dụng train. Test chỉ được dùng để đánh giá cuối và đối chiếu liên kỹ thuật. `Distance(mi)` bị loại vì mô tả chiều dài đoạn đường đã bị ảnh hưởng, không phù hợp với mục tiêu nhận diện sớm. Có 7.236 dòng thiếu thời gian được giữ là `Unknown`, không bị gán ngầm thành ngày thường.

Ba lớp bằng chứng được kết hợp như sau:

| Lớp bằng chứng | Trả lời điều gì? | Đầu ra dùng để tổng hợp |
|---|---|---|
| Luật kết hợp | Tổ hợp điều kiện ngắn nào đồng xuất hiện với Severity 3-4? | Antecedent, coverage, confidence, lift |
| Phân lớp nhị phân | Mỗi sự cố được đánh giá rủi ro ra sao và model sai ở đâu? | `risk_severe`, precision, recall, false negative/positive |
| Thống kê và phân tầng | Chênh lệch có bền ngoài train và có bị nguồn/bang chi phối không? | Nhóm đối chứng, bootstrap CI 95%, audit Source/State/năm |

### 3.1.2. Kết hợp kỹ thuật để trả lời Q1

**Q1: Trong các sự cố được ghi nhận tại California và Texas, tổ hợp điều kiện nào liên hệ với tỷ lệ Severity 3-4 cao hơn, và xu hướng có nhất quán theo nguồn/bang không?**

Luật kết hợp được dùng để phát hiện tổ hợp trên train. Mười antecedent cuối được khóa trước khi xem test. Khi áp dụng lên test, nhóm không chỉ tính confidence/lift mà còn so tỷ lệ Severity 3-4 với nhóm **không thỏa** antecedent, tính bootstrap CI 95%, đối chiếu score mô hình và kiểm tra từng tầng Source/State đủ mẫu.

Ba ví dụ có bằng chứng tương đối mạnh là:

| Rule | Tổ hợp điều kiện | Số test | Tỷ lệ 3-4 trong nhóm | Nhóm không thỏa | Lift test | Risk model trong nhóm | Kết quả phân tầng |
|---|---|---:|---:|---:|---:|---:|---|
| R01 | Junction + nhiệt độ vừa | 662 | 25,83% | 17,33% | 1,461 | 23,05% | 3/3 tầng đủ mẫu cùng chiều |
| R03 | Ban ngày + cuối tuần + nhiệt độ vừa | 755 | 26,49% | 17,25% | 1,498 | 20,01% | 4/4 tầng đủ mẫu cùng chiều |
| R09 | Cuối tuần + nhiệt độ vừa | 1.134 | 25,49% | 17,09% | 1,441 | 19,94% | 4/4 tầng đủ mẫu cùng chiều |

Ví dụ R01 bao phủ 662 sự cố test, trong đó 171 sự cố thuộc Severity 3-4. Tỷ lệ 25,83% cao hơn 8,50 điểm phần trăm so với nhóm không thỏa R01; CI bootstrap 95% của chênh lệch là 5,33-11,72 điểm phần trăm. Score mô hình cũng cao hơn nhóm đối chứng 5,66 điểm phần trăm, với CI 95% là 4,74-6,46 điểm phần trăm. Vì vậy R01 có bằng chứng đồng hướng từ luật, model và kiểm tra thống kê trong phạm vi test.

Tuy nhiên, Q1 không được trả lời chỉ bằng kết quả mẫu gộp. R04 và R08 có lift test xấp xỉ 1,40 nhưng đảo chiều quan sát trong Source2. Hai luật này bị loại khỏi nhóm phát hiện chính. Kết luận Q1 ở giai đoạn hiện tại là: có tám luật ứng viên đồng hướng và ổn định trong các tầng chính đủ mẫu; chưa có căn cứ nói các điều kiện đó gây ra Severity cao.

### 3.1.3. Kết hợp kỹ thuật để trả lời Q2

**Q2: Có thể nhận diện nhóm Severity 3-4 từ thông tin ban đầu đến mức nào, và mô hình thường bỏ sót hoặc cảnh báo nhầm ở đâu?**

Mô hình chính dự báo trực tiếp `is_severe`, cùng biến đích với consequent `MucDo_Nang` của luật. Decision Tree cân bằng được chọn bằng average precision qua 5-fold stratified CV trên train; test không tham gia lựa chọn.

| Mô hình | AP test | Precision 3-4 | Recall 3-4 | F1 3-4 | Balanced accuracy |
|---|---:|---:|---:|---:|---:|
| Decision Tree balanced | 0,3668 | 30,06% | 67,52% | 41,60% | 66,89% |
| Logistic Regression balanced | 0,2794 | 25,26% | 73,81% | 37,64% | 63,45% |
| Dummy prior | 0,1768 | 0,00% | 0,00% | 0,00% | 50,00% |

Decision Tree nhận diện đúng 1.910/2.829 sự cố Severity 3-4, bỏ sót 919 và tạo 4.444 cảnh báo nhầm. Recall 67,52% đi kèm precision chỉ 30,06%, nên model có thể tạo tín hiệu phân tích nhưng chưa đủ chất lượng để tự động ra quyết định.

Luật kết hợp bổ sung góc nhìn về lỗi theo nhóm. Recall của model trong R03 là 62,00% và trong R09 là 65,05%, thấp hơn recall toàn test; trong khi recall trong R06 (`Junction + ngày thường`) là 73,98%. Chênh lệch này cho biết lỗi không phân bố hoàn toàn đồng đều theo các tổ hợp có thể diễn giải. Tuy nhiên, chưa nhóm nào đủ bằng chứng để gọi là “điểm mù chắc chắn”; kết luận cuối phải chờ phân tích false negative và Balanced Random Forest ở Mục 4.

### 3.1.4. Kết hợp kỹ thuật để trả lời Q3

**Q3: Luật và mô hình đồng hướng, bổ sung hoặc cảnh báo giới hạn của nhau ở những nhóm nào?**

Với mỗi antecedent, nhóm nối các `ID` test tương ứng với dự báo, rồi so cả tỷ lệ quan sát và score mô hình với nhóm không thỏa luật. Bảng sau là đầu ra trung tâm của phần tổng hợp:

| Rule | Antecedent | Coverage | Tỷ lệ 3-4 | Nhóm không thỏa | Lift | Risk model | Recall trong rule | Quan hệ |
|---|---|---:|---:|---:|---:|---:|---:|---|
| R01 | Junction + nhiệt độ vừa | 4,14% | 25,83% | 17,33% | 1,461 | 23,05% | 73,68% | Đồng hướng, ổn định theo tầng |
| R02 | Cuối tuần + nhiều mây | 5,32% | 24,32% | 17,31% | 1,376 | 19,37% | 66,18% | Đồng hướng, ổn định theo tầng |
| R03 | Ban ngày + cuối tuần + nhiệt độ vừa | 4,72% | 26,49% | 17,25% | 1,498 | 20,01% | 62,00% | Đồng hướng, ổn định theo tầng |
| R04 | Buổi sáng + nhiệt độ vừa + nhiều mây | 4,99% | 24,69% | 17,31% | 1,396 | 22,62% | 77,16% | Đồng hướng mẫu gộp, không ổn định theo tầng |
| R05 | Ban ngày + Junction + ngày thường | 4,59% | 24,66% | 17,35% | 1,395 | 22,48% | 74,59% | Đồng hướng, ổn định theo tầng |
| R06 | Junction + ngày thường | 6,78% | 24,79% | 17,16% | 1,402 | 21,87% | 73,98% | Đồng hướng, ổn định theo tầng |
| R07 | Trưa-chiều + nhiệt độ vừa + nhiều mây | 4,94% | 23,04% | 17,40% | 1,303 | 21,42% | 73,63% | Đồng hướng, ổn định theo tầng |
| R08 | Ngày thường + nhiệt độ vừa + nhiều mây | 12,09% | 24,81% | 16,70% | 1,403 | 22,38% | 78,13% | Đồng hướng mẫu gộp, không ổn định theo tầng |
| R09 | Cuối tuần + nhiệt độ vừa | 7,09% | 25,49% | 17,09% | 1,441 | 19,94% | 65,05% | Đồng hướng, ổn định theo tầng |
| R10 | Ban ngày + Junction | 5,91% | 24,74% | 17,24% | 1,399 | 21,43% | 72,22% | Đồng hướng, ổn định theo tầng |

Trong mười luật, tám luật đồng hướng ở mẫu gộp và trong mọi tầng Source/State đủ ít nhất 100 sự cố ở cả nhóm luật lẫn nhóm đối chứng. R04 và R08 chỉ đồng hướng trên mẫu gộp. Kết quả này trực tiếp trả lời Q3: model hỗ trợ đánh giá ở cấp từng sự cố, luật cung cấp cấu trúc điều kiện dễ đọc, còn kiểm tra phân tầng chỉ ra nơi kết luận tổng hợp không bền.

## 3.2. Mỗi kỹ thuật bổ sung / xác nhận / mâu thuẫn với kỹ thuật khác ra sao

### 3.2.1. Luật kết hợp bổ sung cho mô hình phân lớp

Mô hình tạo score cho từng sự cố nhưng bản thân score không cho người dùng biết một tổ hợp ngắn nào đang được xem xét. Luật bổ sung antecedent, coverage và lift, nhờ đó chuyển một phần kết quả dự báo thành nhóm điều kiện có thể kiểm tra. Chẳng hạn, R01 cho biết nhóm `Junction + nhiệt độ vừa` có 662 sự cố test và tỷ lệ Severity 3-4 cao hơn nhóm đối chứng 8,50 điểm phần trăm.

Luật còn giúp chia nhỏ lỗi mô hình. Recall thay đổi từ 62,00% ở R03 đến 73,98% ở R06, trong khi recall toàn test là 67,52%. Vì vậy luật cung cấp đầu vào cụ thể cho bước phân tích false negative và kỹ thuật nâng cao, thay vì chỉ kết luận model “tốt” hoặc “kém” từ một metric trung bình.

### 3.2.2. Mô hình phân lớp xác nhận theo nghĩa đồng hướng và bổ sung cho luật

Trong khung báo cáo, từ “xác nhận” được hiểu thận trọng là **bằng chứng đồng hướng**, không phải kiểm chứng độc lập. Rule và model cùng học từ một snapshot và chia sẻ nhiều đặc trưng, nên không thể xem model là một nguồn dữ liệu độc lập xác nhận quan hệ nhân quả.

Với tám luật ổn định, nhóm thỏa antecedent có cả tỷ lệ Severity 3-4 quan sát và `risk_severe` trung bình cao hơn nhóm không thỏa trong mọi tầng Source/State đủ mẫu. Model vì vậy bổ sung hai thông tin mà luật không có:

- score liên tục ở cấp từng `ID`, thay vì chỉ cho biết có/không thỏa antecedent;
- recall và false negative trong nhóm luật, cho biết một pattern có tỷ lệ cao nhưng model nhận diện được đến đâu.

Mức đồng hướng này làm bằng chứng mạnh hơn việc chỉ báo confidence/lift trên train, nhưng vẫn chỉ là quan hệ quan sát.

### 3.2.3. Kiểm tra phân tầng phát hiện mâu thuẫn với kết quả mẫu gộp

Tỷ lệ Severity 3-4 khác mạnh theo nguồn: Source1 là 4,36%, Source2 là 35,36% và Source3 là 35,28%. Vì vậy một luật có thể đạt lift cao do thành phần nguồn khác nhau giữa nhóm luật và nhóm đối chứng.

Hai mâu thuẫn quan trọng là:

- R04: trong Source2, nhóm thỏa luật có tỷ lệ 32,12%, thấp hơn 35,68% của nhóm không thỏa.
- R08: trong Source2, nhóm thỏa luật có tỷ lệ 34,93%, thấp hơn 35,49% của nhóm không thỏa.

Như vậy, kết quả phân tầng mâu thuẫn với hướng tăng của mẫu gộp. R04 và R08 không được dùng làm phát hiện hoặc khuyến nghị chính. Đây là đóng góp thực chất của tổng hợp liên kỹ thuật: một kết quả bổ sung không chỉ làm câu chuyện mạnh hơn mà còn có thể buộc nhóm giảm mức độ khẳng định.

### 3.2.4. Kết luận tổng hợp

Ba kỹ thuật tạo một chuỗi lập luận thống nhất:

1. Luật kết hợp phát hiện và mô tả tổ hợp điều kiện.
2. Mô hình định lượng score và lỗi ở cấp sự cố trong chính các nhóm luật.
3. Bootstrap và phân tầng kiểm tra xem hướng kết quả có bền ngoài train và trước khác biệt Source/State hay không.

Kết quả hiện tại cung cấp tám ứng viên phát hiện ổn định và hai ví dụ mâu thuẫn cần loại khỏi kết luận chính. Phần này chưa chứng minh nguyên nhân và chưa đủ để đưa ra khuyến nghị chính sách. Mục 4 phải tiếp tục từ hạn chế có bằng chứng là 919 false negative và 4.444 false positive, áp dụng Balanced Random Forest trên cùng split/feature/metric, rồi Mục 5 mới chốt 3-5 phát hiện cuối.
