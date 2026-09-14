# Hợp đồng dữ liệu đồ án US Accidents

## 1. Nguồn, đơn vị và phạm vi mẫu

- Tệp nguồn duy nhất cho notebook tổng hợp: `data/accidents_preprocessed.csv`.
- Quy mô snapshot kế thừa từ Bài 1: 80.000 sự cố giao thông, 48 thuộc tính.
- Đơn vị quan sát: một sự cố giao thông được ghi nhận; khóa `ID` đầy đủ và duy nhất.
- Phạm vi địa lý thực tế: California (59.903 dòng) và Texas (20.097 dòng). Không gọi đây là mẫu đại diện cho toàn nước Mỹ.
- Nguồn dữ liệu thô không có trong repository. Đồ án bắt đầu từ snapshot đã được duyệt ở Bài 1 và không lặp lại bước chọn/làm sạch dữ liệu.

## 2. Ý nghĩa nhãn và câu hỏi dự báo

Theo mô tả của bộ US Accidents, `Severity` biểu thị mức ảnh hưởng của sự cố đối với luồng giao thông. Nhãn này không cho biết số người bị thương, tử vong hay thiệt hại tài sản.

| Trường | Định nghĩa vận hành | Vai trò trong đồ án |
|---|---|---|
| `Severity` | Mức ảnh hưởng giao thông từ 1 đến 4 | Nhãn bốn lớp dùng làm nền kỹ thuật và phân tích bổ sung |
| `is_severe` | 1 nếu `Severity` thuộc 3-4, ngược lại là 0 | Nhãn nhị phân chính để dự báo và đối chiếu luật |
| `MucDo_Nang` | Item Boolean tương đương `is_severe = 1` | Consequent của luật kết hợp |
| `MucDo_Nhe` | Item Boolean tương đương `is_severe = 0` | Item đối chứng trong transaction |

Tên `is_severe` và `MucDo_Nang` được giữ để tương thích với mã Bài 1/Bài 3. Trong báo cáo phải diễn giải là **nhóm Severity 3-4 có mức ảnh hưởng giao thông cao**, không diễn giải thành tai nạn có thương vong nặng.

Phân bố snapshot: Severity 1 = 520; Severity 2 = 65.334; Severity 3 = 13.439; Severity 4 = 707. Nhóm Severity 3-4 chiếm 17,68%.

### Câu hỏi dẫn dắt đã khóa

1. **Q1:** Trong các sự cố được ghi nhận tại California và Texas, những tổ hợp điều kiện thời gian, thời tiết, ánh sáng và hạ tầng nào liên hệ với tỷ lệ `Severity 3-4` cao hơn, và xu hướng đó có ổn định theo nguồn dữ liệu và bang không?
2. **Q2:** Có thể nhận diện ngay tại thời điểm ghi nhận ban đầu các sự cố có khả năng thuộc nhóm `Severity 3-4` đến mức nào, và mô hình thường bỏ sót hoặc cảnh báo nhầm trong những nhóm điều kiện nào?
3. **Q3:** Các luật điều kiện bổ sung, cho bằng chứng đồng hướng hoặc mâu thuẫn với đánh giá của mô hình phân lớp như thế nào?

Các câu hỏi này là chuỗi văn bản chuẩn dùng trong README, notebook, Phiếu đề xuất và báo cáo. Chỉ thay đổi khi nhóm lập một quyết định mới và cập nhật đồng thời mọi tài liệu liên quan.

## 3. Đặc trưng phân lớp được phép dùng

```text
Temperature(F), Humidity(%), Pressure(in), Visibility(mi),
Wind_Speed(mph), Precipitation(in), Hour_of_Day, Is_Weekend,
Amenity, Bump, Crossing, Give_Way, Junction, No_Exit, Railway,
Roundabout, Station, Stop, Traffic_Calming, Traffic_Signal,
Infra_Feature_Count
```

Median imputation và scaling phải nằm trong pipeline, chỉ fit trên train. `Is_Weekend` thiếu được impute trong pipeline khi cần cho mô hình; transaction phải giữ trạng thái thiếu thành `Unknown`.

## 4. Biến bị loại và lý do

- `ID`: chỉ dùng nối kết và truy vết.
- `Severity`, `is_severe`, `MucDo_Nang`, `MucDo_Nhe`: là nhãn.
- `Distance(mi)`: mô tả chiều dài đoạn đường bị ảnh hưởng bởi sự cố, có thể chỉ hoàn chỉnh sau khi sự cố xảy ra; loại khỏi bài toán nhận diện sớm để tránh dùng biến hậu nghiệm/gần nhãn.
- `Description`, `End_Time` và các trường chỉ biết sau sự cố: không phù hợp với mục tiêu nhận diện sớm.
- `Street`, `Zipcode`, `Airport_Code` và mã địa chỉ chi tiết: không dùng trong baseline để giảm học thuộc vị trí.
- `Source`, `State`, `Accident_Year`: không đưa vào baseline chính; chỉ dùng kiểm tra thiên lệch và độ bền theo tầng.

## 5. Chất lượng thời gian kế thừa

- Snapshot có 7.236 dòng thiếu `Start_Time` và `Hour_of_Day` sau bước tiền xử lý Bài 1.
- Các dòng này trước đây có nguy cơ bị gán ngầm thành `Is_Weekend=False`. Notebook đồ án tái tạo `Is_Weekend` dạng nullable và giữ chúng là thiếu/`Unknown`.
- Không thể phục hồi thời gian gốc nếu chưa có lại raw snapshot. Kết quả liên quan giờ/ngày phải nêu rõ giới hạn này.

## 6. Quy tắc tạo transaction

- Một `ID` tương ứng một transaction.
- Hạ tầng: giữ các cờ Boolean đủ support trên train.
- Giờ: `Sang` 05-10; `Trua_Chieu` 11-16; `Toi` 17-20; `Dem` 21-04; thiếu là `Unknown`.
- Ngày: `CuoiTuan`, `NgayThuong`; thiếu là `Unknown`.
- Nhiệt độ: dùng `Temperature_Bin` kế thừa từ Bài 1; thiếu là `Unknown`.
- Thời tiết: `Tuyet_Bang`, `Mua`, `Suong_Mu`, `Bao`, `Nhieu_May`, `Quang_Dang`, `Khac`, `Unknown` theo quy tắc Bài 1.
- Ánh sáng: `Day`, `Night`, `Unknown` từ `Sunrise_Sunset`.
- Nhãn transaction: `MucDo_Nang` hoặc `MucDo_Nhe` theo Mục 2.
- Item có support train dưới 0,1% bị loại. Ngưỡng khai phá và luật cuối được chọn trên train; test chỉ dùng đánh giá độ bền.

## 7. Chia dữ liệu, mô hình và đánh giá

- Chia train/test 80/20 theo `ID`, stratify theo bốn lớp `Severity`, `random_state=42`.
- Lưu split tại `artifacts/split_us_accidents.csv`; không ghép CSV theo vị trí dòng.
- Mô hình chính dự báo trực tiếp `is_severe`; chọn bằng average precision qua 5-fold stratified CV trên train.
- Phân lớp bốn mức được giữ làm kết quả nền, chọn bằng F1-macro CV, không dùng làm score chính để đối chiếu luật.
- Imputer, scaler, calibration, mô hình, khai phá và chọn luật chỉ được fit trên train.
- Test chỉ dùng cho đánh giá cuối, đối chiếu rules-model và kiểm tra độ bền.

## 8. Kiểm tra thiên lệch và phạm vi kết luận

- Bắt buộc báo cáo tỷ lệ Severity 3-4 theo `Source`, `State`, `Accident_Year` và trạng thái có/thiếu thời gian.
- Một luật chỉ được gọi là **đồng hướng và ổn định ở các tầng chính** khi chênh lệch quan sát và chênh lệch score mô hình cùng dương trong mọi tầng Source/State đủ ít nhất 100 mẫu ở cả nhóm luật và nhóm đối chứng.
- Luật đảo chiều ở một tầng chính không được dùng làm phát hiện chủ đạo dù kết quả mẫu gộp đẹp.
- Mọi kết quả chỉ là liên hệ quan sát trong snapshot CA/TX. Luật, feature importance và score mô hình không chứng minh nhân quả, không đo thương vong và không tự động khái quát sang vùng hoặc thời kỳ khác.
