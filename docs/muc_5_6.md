# 5. Phát hiện và diễn giải

Các kết quả dưới đây được rút ra từ 16.000 sự cố trong tập test chung. Luật được chọn hoàn toàn trên train rồi mới áp dụng lên test; tỷ lệ của nhóm thỏa antecedent được so với nhóm không thỏa cùng điều kiện. Vì các luật có thể chồng lấp và model với luật cùng học từ một snapshot, các kết quả được gọi là bằng chứng đồng hướng, không phải xác nhận độc lập hay quan hệ nhân quả.

## 5.1. Trả lời từng câu hỏi dẫn dắt

**Q1 — Trong các sự cố được ghi nhận tại California và Texas, những tổ hợp điều kiện thời gian, thời tiết, ánh sáng và hạ tầng nào liên hệ với tỷ lệ Severity 3–4 cao hơn, và xu hướng đó có ổn định theo nguồn dữ liệu và bang không?** Trên tập test, cả 10 luật ứng viên đều có tỷ lệ Severity 3–4 cao hơn nhóm đối chứng khi xét mẫu gộp, với lift từ 1,303 đến 1,498. Sau khi kiểm tra các tầng Source và State đủ ít nhất 100 sự cố ở cả nhóm luật lẫn nhóm đối chứng, 8 luật giữ được chênh lệch quan sát và chênh lệch risk model cùng dương. Hai ví dụ nổi bật là R01 (`Junction + nhiệt độ vừa`) và R03 (`ban ngày + cuối tuần + nhiệt độ vừa`). R04 và R08 không được dùng làm phát hiện tích cực chính vì đảo chiều quan sát tại Source2.

**Mức độ tin cậy Q1 — Khá trong snapshot hiện tại:** R01 và R03 có CI 95% của chênh lệch tỷ lệ nằm hoàn toàn trên 0 và cùng chiều ở lần lượt 3/3 và 4/4 tầng Source/State đủ mẫu. Mức tin cậy giảm khi khái quát ngoài CA/TX hoặc sang thời gian và nguồn ghi nhận mới.

**Q2 — Có thể nhận diện ngay tại thời điểm ghi nhận ban đầu các sự cố có khả năng thuộc nhóm Severity 3–4 đến mức nào, và mô hình thường bỏ sót hoặc cảnh báo nhầm trong những nhóm điều kiện nào?** Decision Tree balanced nhận diện đúng 1.910/2.829 sự cố Severity 3–4, tương ứng recall 67,52%, nhưng precision chỉ 30,06%; mô hình bỏ sót 919 sự cố và tạo 4.444 cảnh báo nhầm. Trong các lát cắt được chọn, R03 (`ban ngày + cuối tuần + nhiệt độ vừa`) là ví dụ nhóm dễ bị bỏ sót hơn: recall chỉ 62,00%, với 76/200 sự cố Severity 3–4 bị bỏ sót. R08 (`ngày thường + nhiệt độ vừa + nhiều mây`) là ví dụ có cảnh báo nhầm cao: 781 false positive, FPR 53,68%. Balanced Random Forest cải thiện AP từ 0,3668 lên 0,3722 và recall từ 67,52% lên 68,96%, giảm false negative từ 919 xuống 878. Đổi lại, precision giảm từ 30,06% xuống 29,29%, F1 giảm từ 41,60% xuống 41,11%, Brier tăng từ 0,1290 lên 0,1301 và false positive tăng thêm 267 trường hợp, lên 4.711. Do đó BRF chỉ là cải thiện biên về xếp hạng/recall, chưa phải mô hình thay thế vượt trội.

**Mức độ tin cậy Q2 — Khá đối với so sánh ngoại tuyến trong snapshot:** Hai mô hình dùng cùng split, feature và quy trình đánh giá; BRF được chọn bằng AP qua 5-fold stratified CV trên train rồi mới đánh giá trên test. Tuy nhiên đây vẫn chỉ là một test split trong cùng snapshot, nên mức tin cậy cho vận hành thực tế hoặc dữ liệu tương lai chỉ ở mức trung bình.

**Q3 — Các luật điều kiện bổ sung, cho bằng chứng đồng hướng hoặc mâu thuẫn với đánh giá của mô hình phân lớp như thế nào?** Luật cung cấp antecedent ngắn, độ phủ và nhóm đối chứng; mô hình cung cấp risk liên tục và hồ sơ FN/FP ở cấp sự cố. Với 8 luật ổn định, tỷ lệ Severity 3–4 quan sát và risk model trung bình đều cao hơn nhóm không thỏa trong các tầng chính đủ mẫu. Tuy nhiên, R08 cho thấy hai kỹ thuật có thể kể một câu chuyện đồng hướng trên mẫu gộp trong khi kiểm tra theo nguồn lại bác bỏ tính ổn định: tại Source2, tỷ lệ quan sát của nhóm R08 là 34,93%, thấp hơn 35,49% ở nhóm đối chứng. Phân tầng vì vậy không chỉ củng cố mà còn giới hạn kết luận.

**Mức độ tin cậy Q3 — Trung bình:** Kết quả 8/10 luật đồng hướng và ổn định ở các tầng chính là bằng chứng nhất quán trong dữ liệu, nhưng luật và mô hình cùng học từ một snapshot nên không phải hai nguồn xác nhận độc lập; R04/R08 còn cho thấy kết luận có thể đổi theo Source.

## 5.2. Các phát hiện chính kèm bằng chứng

| Card | Phát hiện/đánh đổi thực tế | Bằng chứng chính | Độ bền và quyết định |
|---|---|---|---|
| E01 — R01 | Nhóm sự cố tại nút giao trong khoảng nhiệt độ vừa có tỷ lệ Severity 3–4 cao hơn, nhưng chỉ bao phủ 4,14% tập test | 662 sự cố; 25,83% so với 17,33%; chênh 8,50 đpt, CI 95% 5,33–11,72; lift 1,461; FN 45; FPR 51,93% | Cùng chiều tại Source1, Source2 và CA (3/3 tầng chính đủ mẫu); giữ làm phát hiện tích cực có phạm vi hẹp |
| E02 — R03 | Nhóm ban ngày, cuối tuần và nhiệt độ vừa có lift cao nhất, nhưng mô hình bỏ sót tương đối nhiều | 755 sự cố; 26,49% so với 17,24%; chênh 9,25 đpt, CI 95% 6,29–12,42; lift 1,498; recall 62,00%; FN 76 | Cùng chiều tại Source1, Source2, CA và TX (4/4 tầng chính đủ mẫu); giữ làm phát hiện tích cực và lát cắt bỏ sót |
| E03 — BRF | Ưu tiên tăng khả năng phát hiện chỉ giảm 41 ca bỏ sót nhưng làm phát sinh thêm 267 cảnh báo nhầm, nên chưa đủ cơ sở thay baseline | Recall 67,52%→68,96%; FN 919→878; precision 30,06%→29,29%; FP 4.444→4.711; F1 và Brier xấu hơn | Cùng split/features, chọn bằng AP CV trên train; giữ như bằng chứng đánh đổi, không gọi là vượt trội |
| E04 — R08 | Kết quả mẫu gộp có thể gây kết luận sai nếu không kiểm tra theo nguồn | 1.935 sự cố; lift 1,403; Source2 đảo chiều 34,93% so với 35,49%; FP 781; FPR 53,68% | Source1, Source2, CA và TX đủ mẫu; Source2 đảo chiều nên chỉ 3/4 tầng cùng chiều; không dùng làm phát hiện tích cực, chỉ giữ làm card giới hạn |

### Evidence card 1 — Nút giao kết hợp nhiệt độ vừa là một tín hiệu ổn định nhưng độ phủ hẹp

- **Khẳng định:** Trong snapshot CA/TX, nhóm thỏa R01 (`Junction + nhiệt độ vừa`) có tỷ lệ Severity 3–4 cao hơn nhóm không thỏa.
- **Bằng chứng luật:** R01 bao phủ 662/16.000 sự cố test (4,14%). Tỷ lệ Severity 3–4 là 25,83%, so với 17,33% ở nhóm đối chứng; chênh lệch 8,50 điểm phần trăm, bootstrap CI 95% từ 5,33 đến 11,72 điểm phần trăm; lift test 1,461.
- **Bằng chứng model:** Risk severe trung bình là 23,06%, so với 17,39% ở nhóm đối chứng; CI 95% của chênh lệch risk từ 4,75 đến 6,46 điểm phần trăm. Recall trong nhóm đạt 73,68%, với 45 ca severe bị bỏ sót; precision 33,07% và FPR 51,93% cho thấy cảnh báo nhầm vẫn cao.
- **Độ bền:** Chênh lệch quan sát và risk model cùng dương tại Source1, Source2 và CA — cả 3/3 tầng Source/State đủ mẫu. Nhóm R01 tại Source3 và TX không đạt ngưỡng tối thiểu 100 sự cố nên không được dùng để khẳng định độ bền.
- **Diễn giải và giới hạn:** Nút giao có thể đại diện cho môi trường giao thông phức tạp, nhiều luồng cắt nhau; tuy nhiên dữ liệu không đo lưu lượng, tốc độ hay loại đường nên chưa thể quy chênh lệch cho bản thân nút giao. Độ phủ 4,14% cũng khiến R01 chỉ phù hợp làm tín hiệu ưu tiên, không phải quy tắc bao quát.

### Evidence card 2 — Ban ngày, cuối tuần và nhiệt độ vừa có lift cao nhất nhưng model bỏ sót tương đối nhiều

- **Khẳng định:** R03 (`ban ngày + cuối tuần + nhiệt độ vừa`) là luật có lift test cao nhất trong 10 ứng viên và giữ cùng chiều ở các tầng chính.
- **Bằng chứng luật:** R03 bao phủ 755 sự cố (4,72%). Tỷ lệ Severity 3–4 đạt 26,49%, so với 17,24% ở nhóm đối chứng; chênh lệch 9,25 điểm phần trăm, CI 95% từ 6,29 đến 12,42 điểm phần trăm; lift test 1,498.
- **Bằng chứng model:** Risk severe trung bình tăng từ 17,51% ở nhóm đối chứng lên 20,01% trong nhóm luật; CI 95% của chênh lệch risk từ 1,70 đến 3,39 điểm phần trăm. Dù vậy recall trong nhóm chỉ 62,00%, thấp hơn recall toàn test 67,52%; 76/200 sự cố Severity 3–4 trong nhóm bị bỏ sót. Precision trong nhóm là 39,24% và FPR là 34,59%.
- **Độ bền:** Cả chênh lệch quan sát lẫn risk model đều dương tại Source1, Source2, CA và TX — đủ 4/4 tầng Source/State đạt ngưỡng mẫu. Source3 không đủ 100 sự cố trong nhóm luật.
- **Diễn giải và giới hạn:** Tổ hợp này hữu ích cho phân tích vì bằng chứng rule mạnh nhưng model chưa bắt hết trường hợp. Không nên diễn giải “cuối tuần” hay “ban ngày” là nguyên nhân; chúng có thể phản ánh kiểu hành trình, lưu lượng, thành phần nguồn hoặc đặc điểm địa bàn chưa được quan sát.

### Evidence card 3 — Giảm 41 ca bỏ sót phải đánh đổi bằng 267 cảnh báo nhầm bổ sung

- **Khẳng định:** Việc ưu tiên tăng khả năng phát hiện bằng BRF chỉ giảm được 41 ca bỏ sót nhưng làm phát sinh thêm 267 cảnh báo nhầm, nên chưa đủ cơ sở để thay thế baseline trong vận hành.
- **Bằng chứng:** So với Decision Tree balanced, BRF tăng AP 0,3668 → 0,3722, ROC AUC 0,7312 → 0,7367 và recall 67,52% → 68,96%; số bỏ sót giảm 41 ca, từ 919 xuống 878. Ngược lại, precision giảm 30,06% → 29,29%, F1 giảm 41,60% → 41,11%, balanced accuracy giảm 66,89% → 66,60%, Brier xấu hơn 0,1290 → 0,1301 và false positive tăng 4.444 → 4.711.
- **Độ bền:** BRF được chọn bằng AP qua 5-fold stratified CV trên train, sử dụng đúng split và feature như baseline; test chỉ dùng để đánh giá sau khi khóa lưới tham số.
- **Diễn giải và giới hạn:** Mất cân bằng lớp chỉ là một phần của vấn đề. Các đặc trưng hiện có thiếu lưu lượng, tốc độ và loại đường chi tiết; ngoài ra nhãn thay đổi mạnh theo Source và năm. Vì vậy cân bằng mẫu không bảo đảm cải thiện chất lượng cảnh báo tổng thể. Kết quả không đủ để gọi BRF là giải pháp vượt trội hoặc tự động hóa quyết định vận hành.

### Evidence card 4 — R08 cảnh báo nguy cơ kết luận sai từ số liệu gộp

- **Khẳng định:** R08 (`ngày thường + nhiệt độ vừa + nhiều mây`) trông mạnh trên mẫu gộp nhưng không ổn định theo nguồn, nên chỉ được giữ như một phát hiện về giới hạn.
- **Bằng chứng mẫu gộp:** R08 bao phủ 1.935 sự cố test (12,09%), lớn nhất trong 10 luật. Tỷ lệ Severity 3–4 là 24,81%, so với 16,70% ở nhóm đối chứng; chênh lệch 8,11 điểm phần trăm, CI 95% từ 6,12 đến 10,22 điểm phần trăm; lift test 1,403. Risk model trung bình cũng tăng từ 16,97% lên 22,38%.
- **Bằng chứng mâu thuẫn:** Source1, Source2, CA và TX là bốn tầng chính đủ mẫu. Trong Source2, nhóm thỏa R08 có tỷ lệ Severity 3–4 là 34,93%, thấp hơn 35,49% của nhóm không thỏa, tức đảo chiều −0,56 điểm phần trăm; vì vậy chỉ 3/4 tầng giữ chênh lệch quan sát dương. Source3 không đủ 100 sự cố trong nhóm luật. Đồng thời FPR trong nhóm R08 lên tới 53,68%, với 781 cảnh báo nhầm.
- **Diễn giải:** Sự khác biệt rất lớn về tỷ lệ nhãn giữa Source1 (4,36%) và Source2 (35,36%) có thể tạo hiệu ứng thành phần khi gộp dữ liệu. Vì vậy R08 không được chuyển thành khuyến nghị; giá trị của nó là minh họa vì sao mọi insight phải qua audit phân tầng.

# 6. Bàn luận

## 6.1. Vì sao kết quả có thể xuất hiện như vậy

Các luật chứa `Junction`, loại ngày, ánh sáng và nhiệt độ có thể đang đại diện cho nhiều cơ chế chưa quan sát. Nút giao thường đi kèm nhiều hướng chuyển động và xung đột luồng, nhưng mức ảnh hưởng còn phụ thuộc lưu lượng, tốc độ, cấp đường, thời gian xử lý và khả năng tổ chức giao thông. Tương tự, cuối tuần hoặc ban ngày có thể gắn với kiểu hành trình và mật độ phương tiện khác ngày thường, chứ không tự thân làm Severity tăng.

Chênh lệch theo Source là lời giải thích thay thế đặc biệt quan trọng. Source1 có tỷ lệ Severity 3–4 chỉ 4,36%, trong khi Source2 và Source3 đều khoảng 35,3%. Một antecedent xuất hiện với tỷ trọng nguồn khác nhau giữa nhóm luật và nhóm đối chứng có thể tạo lift cao ở mẫu gộp dù liên hệ yếu hoặc đảo chiều trong từng nguồn. Trường hợp R08 tại Source2 là bằng chứng trực tiếp cho nguy cơ này.

Kết quả BRF cải thiện ít cho thấy mất cân bằng lớp không phải hạn chế duy nhất. Undersampling trong từng cây giúp model chú ý hơn đến lớp 3–4 nên recall tăng, nhưng đồng thời làm nhiều mẫu 1–2 bị gắn nhãn dương hơn. Khi feature không chứa đủ thông tin phân biệt và nhãn biến động theo nguồn/thời gian, tăng độ nhạy thường phải trả giá bằng precision và false positive.

## 6.2. Tương quan và nhân quả

Thiết kế hiện tại là quan sát hồi cứu trên các sự cố đã được ghi nhận. Luật kết hợp đo đồng xuất hiện và model tối ưu khả năng dự báo; cả hai đều không tạo ra đối chứng ngẫu nhiên và không kiểm soát đầy đủ biến nhiễu. Do đó, phát biểu hợp lệ là một tổ hợp “liên hệ với” hoặc “đi cùng” tỷ lệ Severity 3–4 cao hơn trong snapshot, không phải tổ hợp đó “gây ra” mức ảnh hưởng cao.

Dữ liệu chỉ gồm các sự cố, không có mẫu những chuyến đi hoặc khoảng thời gian không xảy ra sự cố. Vì thiếu mẫu số phơi nhiễm, tỷ lệ trong báo cáo là tỷ lệ Severity 3–4 có điều kiện trên sự cố đã được ghi nhận, không phải xác suất xảy ra tai nạn đối với người lái xe. Các biến Source, địa bàn, năm, loại đường và lưu lượng có thể đồng thời ảnh hưởng cả antecedent lẫn nhãn; đây là các đường gây nhiễu chưa được mô hình hóa đầy đủ.

Vì vậy, các phát hiện không đủ căn cứ để thay đổi hạ tầng, quy kết nguyên nhân hoặc tự động điều động nguồn lực. Chúng phù hợp hơn với vai trò tín hiệu để ưu tiên rà soát, thu thập thêm dữ liệu và thiết kế kiểm định tiền cứu theo thời gian hoặc địa bàn mới.

## 6.3. Giới hạn và thiên lệch

1. **Ý nghĩa nhãn:** `Severity` đo mức ảnh hưởng lên luồng giao thông, không đo số người bị thương, tử vong hay thiệt hại tài sản. Không được gọi nhóm 3–4 là tai nạn gây thương vong nặng.
2. **Phạm vi địa lý:** Snapshot chỉ gồm California (59.903 sự cố) và Texas (20.097), không đại diện cho toàn Hoa Kỳ hoặc các bang khác.
3. **Thiên lệch nguồn:** Tỷ lệ Severity 3–4 khác mạnh giữa Source1 (4,36%) và Source2/3 (khoảng 35,3%). R08 đảo chiều tại Source2 cho thấy kết quả gộp có thể bị chi phối bởi thành phần nguồn.
4. **Biến động theo thời gian:** Tỷ lệ Severity 3–4 giảm từ khoảng 34–36% trong giai đoạn 2016–2018 xuống 0,39% năm 2023. Điều này có thể phản ánh drift thực, thay đổi phạm vi hoặc quy trình ghi nhận; split ngẫu nhiên 80/20 không thay thế kiểm định trên tương lai.
5. **Thiếu thời gian:** Có 7.236 dòng thiếu `Start_Time`; nhóm thiếu thời gian chỉ có 0,95% Severity 3–4, so với 19,35% ở nhóm có thời gian. Các luật giờ/ngày không bao phủ đúng nhóm này và chưa thể phục hồi nếu thiếu dữ liệu thô.
6. **Thiếu biến giải thích:** Dữ liệu chưa có lưu lượng, tốc độ trước sự cố, loại đường chi tiết, thời gian phản ứng và các yếu tố phơi nhiễm. `Distance(mi)` bị loại có chủ đích vì có thể là thông tin hậu nghiệm.
7. **Phụ thuộc lựa chọn kỹ thuật:** Luật thay đổi theo cách rời rạc hóa, ngưỡng support/confidence/lift và quy tắc loại dư thừa. Các luật còn có thể chồng lấp nên không được cộng số mẫu hoặc số lỗi giữa các evidence card.
8. **Khả năng dự báo còn hạn chế:** Baseline có precision 30,06%; BRF chỉ cải thiện AP/recall ở mức biên và làm tăng false positive. Cả hai chỉ là tín hiệu phân tích ngoại tuyến, chưa phải xác suất vận hành được xác nhận ngoài mẫu.
9. **Khả năng khái quát:** Đánh giá hiện tại dùng một split ngẫu nhiên trong cùng snapshot. Cần kiểm định theo thời gian, nguồn và địa bàn mới trước khi triển khai thực tế.

## Nhật ký quyết định 

| Ngày | Quyết định | Phương án thay thế | Bằng chứng đã xem | Lý do chọn | Ảnh hưởng đến kết luận |
|---|---|---|---|---|---|
| 2026-09-15 | Chọn 4 evidence cards: R01, R03, đánh đổi BRF và giới hạn R08 | Chuyển cả 10 luật thành insight độc lập | `rules_model_test.csv`, audit phân tầng và bảng before/after | Bao phủ Q1–Q3, giảm trùng lặp và bắt buộc có một phát hiện về giới hạn | Kết luận tập trung vào hai pattern ổn định, một giới hạn mô hình và một cảnh báo thiên lệch |
| 2026-09-15 | Không dùng R04/R08 làm phát hiện tích cực hoặc khuyến nghị | Giữ vì lift mẫu gộp cao | R04/R08 đảo chiều quan sát tại Source2 | Tránh hiệu ứng gộp che khuất khác biệt theo nguồn | R08 chỉ được dùng để minh họa giới hạn; mức khẳng định của Q1 giảm |
| 2026-09-15 | Kết luận BRF là cải thiện biên, không phải mô hình vượt trội | Chọn BRF chỉ vì AP và recall tăng | FN giảm 41 nhưng FP tăng 267; precision, F1, balanced accuracy và Brier đều xấu hơn | Báo cáo đầy đủ đánh đổi thay vì chỉ chọn metric tăng | Không đề xuất thay baseline hoặc tự động hóa quyết định chỉ từ kết quả BRF |

## Dàn ý thuyết trình phần của Chiến (khoảng 2 phút)

“Phần phát hiện được chốt từ dữ liệu test, không lấy metric train để kể insight. Nhóm giữ hai pattern ổn định. Thứ nhất, R01 — nút giao kết hợp nhiệt độ vừa — có tỷ lệ Severity 3–4 là 25,83%, cao hơn 17,33% của nhóm đối chứng; lift 1,461 và giữ cùng chiều trong các tầng chính đủ mẫu. Thứ hai, R03 — ban ngày, cuối tuần và nhiệt độ vừa — có lift test cao nhất 1,498, nhưng recall model trong nhóm chỉ 62%, cho thấy luật còn giúp phát hiện một lát cắt mà model bỏ sót tương đối nhiều.

Về kỹ thuật nâng cao, Balanced Random Forest chỉ cải thiện biên: recall tăng từ 67,52% lên 68,96% và giảm 41 ca bỏ sót, nhưng false positive tăng thêm 267 và precision giảm xuống 29,29%. Vì vậy nhóm không gọi BRF là vượt trội.

Điểm quan trọng nhất về giới hạn là R08. Trên mẫu gộp luật này có lift 1,403, nhưng tại Source2 tỷ lệ nhóm luật lại thấp hơn nhóm đối chứng 0,56 điểm phần trăm. Điều đó cho thấy kết quả gộp có thể bị thiên lệch nguồn. Toàn bộ phát hiện chỉ là liên hệ quan sát trong snapshot CA/TX; Severity đo ảnh hưởng giao thông, không đo thương vong, và chưa đủ căn cứ để suy luận nhân quả hay tự động ra quyết định.”
