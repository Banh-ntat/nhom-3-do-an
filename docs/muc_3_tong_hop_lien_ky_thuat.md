# 3. Tổng hợp liên kỹ thuật

> Bản nội dung kỹ thuật để đưa vào báo cáo. Các số liệu được sinh từ `phan-tich-tong-hop.ipynb`; không thay đổi số liệu bằng cách nhập tay.

### Phạm vi trả lời của Mục 3

Mục 3 không phải phần liệt kê lại kết quả của hai bài tập. Phần này dùng cùng các sự cố test để trả lời ba câu hỏi dẫn dắt bằng cách đối chiếu luật, dự báo và kiểm tra độ bền. Trạng thái trả lời sau bước D.6 được hiểu như sau:

| Câu hỏi | Mục 3 đã trả lời được gì? | Phần tiếp theo phải làm gì? |
|---|---|---|
| Q1 | **Đã có câu trả lời kỹ thuật:** xác định được 8/10 luật ứng viên có tỷ lệ Severity 3-4 cao hơn nhóm đối chứng và đồng hướng trong các tầng Source/State đủ mẫu. | Mục 5 chọn 3-5 phát hiện có ý nghĩa thực tế từ các luật ổn định; không thay đổi số liệu Q1. |
| Q2 | **Đã trả lời baseline:** định lượng được khả năng nhận diện, tổng số bỏ sót/cảnh báo nhầm và lỗi trong từng nhóm luật. | Mục 4 phân tích sâu false negative và thử Balanced Random Forest; nếu chọn mô hình mới thì cập nhật câu trả lời cuối về khả năng nhận diện. |
| Q3 | **Đã có câu trả lời với baseline:** 8 luật đồng hướng và ổn định; R04/R08 đồng hướng ở mẫu gộp nhưng mâu thuẫn trong Source2. | Nếu Mục 4 thay mô hình chính, chạy lại cùng bảng đối chiếu để xác nhận quan hệ còn giữ nguyên. |

Do đó, Mục 3 đủ để bàn giao sang bước D.7. Không cần chờ phần sau mới biết câu trả lời của Q1 và Q3; chỉ Q2 chưa phải kết luận mô hình cuối.

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

**Q1: Trong các sự cố được ghi nhận tại California và Texas, những tổ hợp điều kiện thời gian, thời tiết, ánh sáng và hạ tầng nào liên hệ với tỷ lệ `Severity 3-4` cao hơn, và xu hướng đó có ổn định theo nguồn dữ liệu và bang không?**

Luật kết hợp được dùng để phát hiện tổ hợp trên train. Mười antecedent cuối được khóa trước khi xem test. Khi áp dụng lên test, nhóm không chỉ tính confidence/lift mà còn so tỷ lệ Severity 3-4 với nhóm **không thỏa** antecedent, tính bootstrap CI 95%, đối chiếu score mô hình và kiểm tra từng tầng Source/State đủ mẫu.

Ba ví dụ có bằng chứng tương đối mạnh là:

| Rule | Tổ hợp điều kiện | Số test | Tỷ lệ 3-4 trong nhóm | Nhóm không thỏa | Lift test | Risk model trong nhóm | Kết quả phân tầng |
|---|---|---:|---:|---:|---:|---:|---|
| R01 | Junction + nhiệt độ vừa | 662 | 25,83% | 17,33% | 1,461 | 23,05% | 3/3 tầng đủ mẫu cùng chiều |
| R03 | Ban ngày + cuối tuần + nhiệt độ vừa | 755 | 26,49% | 17,25% | 1,498 | 20,01% | 4/4 tầng đủ mẫu cùng chiều |
| R09 | Cuối tuần + nhiệt độ vừa | 1.134 | 25,49% | 17,09% | 1,441 | 19,94% | 4/4 tầng đủ mẫu cùng chiều |

Ví dụ R01 bao phủ 662 sự cố test, trong đó 171 sự cố thuộc Severity 3-4. Tỷ lệ 25,83% cao hơn 8,50 điểm phần trăm so với nhóm không thỏa R01; CI bootstrap 95% của chênh lệch là 5,33-11,72 điểm phần trăm. Score mô hình cũng cao hơn nhóm đối chứng 5,66 điểm phần trăm, với CI 95% là 4,74-6,46 điểm phần trăm. Vì vậy R01 có bằng chứng đồng hướng từ luật, model và kiểm tra thống kê trong phạm vi test.

Tuy nhiên, Q1 không được trả lời chỉ bằng kết quả mẫu gộp. R04 và R08 có lift test xấp xỉ 1,40 nhưng đảo chiều quan sát trong Source2. Hai luật này bị loại khỏi nhóm phát hiện chính.

**Câu trả lời hiện tại cho Q1:** trong snapshot CA/TX, các tổ hợp như `Junction + nhiệt độ vừa`, `ban ngày + cuối tuần + nhiệt độ vừa` và `cuối tuần + nhiệt độ vừa` liên hệ với tỷ lệ Severity 3-4 cao hơn nhóm không thỏa điều kiện. Tổng cộng 8/10 luật ứng viên giữ cùng chiều trong các tầng Source/State đủ mẫu. Đây là các liên hệ quan sát dùng để ưu tiên điều tra và giám sát, không phải bằng chứng rằng các điều kiện trên gây ra Severity cao.

### 3.1.3. Kết hợp kỹ thuật để trả lời Q2

**Q2: Có thể nhận diện ngay tại thời điểm ghi nhận ban đầu các sự cố có khả năng thuộc nhóm `Severity 3-4` đến mức nào, và mô hình thường bỏ sót hoặc cảnh báo nhầm trong những nhóm điều kiện nào?**

Mô hình chính dự báo trực tiếp `is_severe`, cùng biến đích với consequent `MucDo_Nang` của luật. Decision Tree cân bằng được chọn bằng average precision qua 5-fold stratified CV trên train; test không tham gia lựa chọn.

| Mô hình | AP test | Precision 3-4 | Recall 3-4 | F1 3-4 | Balanced accuracy |
|---|---:|---:|---:|---:|---:|
| Decision Tree balanced | 0,3668 | 30,06% | 67,52% | 41,60% | 66,89% |
| Logistic Regression balanced | 0,2794 | 25,26% | 73,81% | 37,64% | 63,45% |
| Dummy prior | 0,1768 | 0,00% | 0,00% | 0,00% | 50,00% |

Decision Tree nhận diện đúng 1.910/2.829 sự cố Severity 3-4, bỏ sót 919 và tạo 4.444 cảnh báo nhầm. Recall 67,52% đi kèm precision chỉ 30,06%, nên model có thể tạo tín hiệu phân tích nhưng chưa đủ chất lượng để tự động ra quyết định.

Để trả lời vế “bỏ sót hoặc cảnh báo nhầm trong nhóm nào”, mỗi antecedent được dùng như một lát cắt lỗi. `FPR` là tỷ lệ sự cố Severity 1-2 bị model cảnh báo nhầm thành 3-4 trong nhóm đang xét. Các nhóm luật có thể chồng lấp, vì vậy không được cộng số lỗi giữa các dòng.

| Phạm vi | Recall 3-4 | Bỏ sót 3-4 | Precision 3-4 | FPR | Ý nghĩa đối với Q2 |
|---|---:|---:|---:|---:|---|
| Toàn bộ test | 67,52% | 919 | 30,06% | 33,74% | Mốc so sánh chung |
| R03: Ban ngày + cuối tuần + nhiệt độ vừa | 62,00% | 76 | 39,24% | 34,59% | Recall thấp hơn mốc chung; cần ưu tiên phân tích nguyên nhân bỏ sót |
| R09: Cuối tuần + nhiệt độ vừa | 65,05% | 101 | 40,09% | 33,25% | Có 101 ca severe bị bỏ sót trong nhóm; recall vẫn thấp hơn mốc chung |
| R05: Ban ngày + Junction + ngày thường | 74,59% | 46 | 31,18% | 53,89% | Recall cao hơn nhưng đổi lại tỷ lệ cảnh báo nhầm rất cao |
| R08: Ngày thường + nhiệt độ vừa + nhiều mây | 78,13% | 105 | 32,44% | 53,68% | Bắt được nhiều severe hơn nhưng cảnh báo nhầm cao; luật còn không bền trong Source2 |

**Câu trả lời hiện tại cho Q2:** baseline nhận diện được khoảng hai phần ba số sự cố Severity 3-4, nhưng chỉ khoảng ba trên mười cảnh báo severe là đúng. R03 và R09 là hai lát cắt cần ưu tiên khi phân tích bỏ sót; R05 và R08 minh họa đánh đổi khi recall cao đi kèm nhiều cảnh báo nhầm. Chưa được gọi các nhóm này là “điểm mù chắc chắn”, vì chúng chồng lấp và chưa kiểm soát đồng thời các yếu tố khác. Mục 4 phải kiểm tra sâu false negative và Balanced Random Forest trước khi chốt mô hình cuối.

### 3.1.4. Kết hợp kỹ thuật để trả lời Q3

**Q3: Các luật điều kiện bổ sung, cho bằng chứng đồng hướng hoặc mâu thuẫn với đánh giá của mô hình phân lớp như thế nào?**

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

Trong mười luật, tám luật đồng hướng ở mẫu gộp và trong mọi tầng Source/State đủ ít nhất 100 sự cố ở cả nhóm luật lẫn nhóm đối chứng. R04 và R08 chỉ đồng hướng trên mẫu gộp.

**Câu trả lời hiện tại cho Q3:** luật bổ sung cho model bằng cách nêu rõ tổ hợp và độ phủ; model cho bằng chứng đồng hướng khi score severe trung bình tăng trong nhóm luật; kiểm tra phân tầng phát hiện mâu thuẫn ở R04/R08 mà kết quả mẫu gộp che khuất. Vì rule và model cùng học từ một snapshot, “đồng hướng” không được gọi là xác nhận độc lập hay bằng chứng nhân quả.

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

Kết quả hiện tại cung cấp tám ứng viên phát hiện ổn định và hai ví dụ mâu thuẫn cần loại khỏi kết luận chính. Như vậy, phần D.2-D.6 và Mục 3 đã hoàn tất đầu ra cần thiết để trả lời Q1, trả lời Q3 với baseline và tạo câu trả lời baseline có bằng chứng cho Q2.

Phần tiếp theo không làm lại Mục 3. Mục 4 nhận đầu vào là 919 false negative, 4.444 false positive và bảng lỗi theo rule để kiểm tra Balanced Random Forest trên cùng split/feature/metric. Nếu mô hình mới được chọn, chỉ cần tái tạo các cột score/lỗi và cập nhật bảng đối chiếu; luật, split và quy trình kiểm tra độ bền được giữ nguyên. Mục 5 sau đó chọn 3-5 phát hiện cuối và viết khuyến nghị. Toàn bộ chuỗi vẫn chỉ phản ánh liên hệ quan sát, chưa chứng minh nguyên nhân hay đủ căn cứ ban hành chính sách.
