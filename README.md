# Đồ án Khai phá dữ liệu - US Accidents

## Chủ đề

Phân tích các tổ hợp điều kiện liên hệ với mức ảnh hưởng giao thông của sự cố tại California và Texas.

`Severity` trong US Accidents biểu thị mức ảnh hưởng lên luồng giao thông, không phải số người bị thương hoặc tử vong. Snapshot phân tích có 80.000 dòng và chỉ gồm California/Texas, nên kết luận không đại diện cho toàn nước Mỹ.

## Câu hỏi dẫn dắt

1. Trong các sự cố được ghi nhận tại California và Texas, những tổ hợp điều kiện thời gian, thời tiết, ánh sáng và hạ tầng nào liên hệ với tỷ lệ `Severity 3-4` cao hơn, và xu hướng đó có ổn định theo nguồn dữ liệu và bang không?
2. Có thể nhận diện ngay tại thời điểm ghi nhận ban đầu các sự cố có khả năng thuộc nhóm `Severity 3-4` đến mức nào, và mô hình thường bỏ sót hoặc cảnh báo nhầm trong những nhóm điều kiện nào?
3. Các luật điều kiện bổ sung, cho bằng chứng đồng hướng hoặc mâu thuẫn với đánh giá của mô hình phân lớp như thế nào?

## Cấu trúc

```text
nhom-3-do-an/
|-- README.md
|-- requirements.txt
|-- data/
|   |-- README.md
|   `-- accidents_preprocessed.csv   # Không commit lên Git
|-- do_an/
|   `-- analysis_core.py
|-- artifacts/                       # Split, metrics, rules, predictions, figures
|-- docs/
|   |-- muc_3_tong_hop_lien_ky_thuat.md
|   `-- nhat_ky_quyet_dinh.md
`-- phan-tich-tong-hop.ipynb
```

## Môi trường

Đã kiểm tra với Python 3.9.13. Cài dependency:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Phiên bản thực tế nằm tại `artifacts/environment.lock.txt`.

## Dữ liệu

Đặt snapshot đã tiền xử lý từ Bài 1 tại:

```text
data/accidents_preprocessed.csv
```

File cần có 80.000 `ID` duy nhất, `Severity` thuộc 1-4 và các trường được mô tả trong `artifacts/data_contract_us_accidents.md`. Dữ liệu CSV được loại khỏi Git; không sử dụng đường dẫn tuyệt đối cá nhân.

## Chạy lại

Trong thư mục gốc repository:

```powershell
python -m nbconvert --to notebook --execute .\phan-tich-tong-hop.ipynb `
  --output phan-tich-tong-hop.ipynb --ExecutePreprocessor.timeout=1200
```

Hoặc mở notebook, chọn kernel của môi trường trên rồi dùng **Restart Kernel & Run All**.

Notebook thực hiện:

1. Kiểm tra data contract, phạm vi và thiên lệch nguồn.
2. Tạo split 80/20 chung theo `ID`, stratify `Severity`, seed 42.
3. Chạy baseline nhị phân chính và nền phân lớp bốn mức.
4. Khai phá luật hoàn toàn trên train.
5. Kiểm định luật trên test, nối dự báo theo `ID` và kiểm tra Source/State/năm.
6. Xuất toàn bộ artifact cho phần tổng hợp liên kỹ thuật.

Imputation, scaling, calibration, lựa chọn mô hình và khai phá luật chỉ fit trên train. `Distance(mi)` bị loại khỏi mô hình nhận diện sớm; 7.236 dòng thiếu thời gian được giữ là `Unknown`.

## Tiến độ

Đã hoàn thành D.2-D.6:

- Split chung và audit dữ liệu.
- Baseline nhị phân/bốn lớp không leakage.
- Luật train và kiểm định test.
- Bảng rules-model và kiểm tra độ bền theo tầng.
- Chẩn đoán bỏ sót và cảnh báo nhầm trong từng nhóm luật.
- Tám luật đồng hướng, ổn định ở các tầng chính; R04/R08 chỉ đồng hướng trên mẫu gộp.

Mức độ trả lời câu hỏi sau D.6:

- Q1 đã có câu trả lời kỹ thuật từ 8 luật ổn định; Mục 5 chỉ chọn và diễn giải các phát hiện cuối.
- Q2 đã có câu trả lời baseline và lát cắt lỗi theo rule; D.7 phải phân tích false negative sâu hơn và kiểm tra Balanced Random Forest trước khi chốt mô hình cuối.
- Q3 đã được trả lời với baseline bằng 8 trường hợp đồng hướng và 2 trường hợp không bền theo nguồn; phải chạy lại bảng đối chiếu nếu D.7 thay mô hình chính.

Bước tiếp theo là D.7: áp dụng Balanced Random Forest theo cùng split, feature và average precision CV; sau đó chốt 3-5 evidence cards và khuyến nghị cuối.

## Kết quả baseline chính

Decision Tree nhị phân đạt average precision 0,3668, precision nhóm 3-4 là 0,3006 và recall 0,6752. Trên 16.000 dòng test, mô hình bỏ sót 919/2.829 mẫu nhóm 3-4 và tạo 4.444 cảnh báo nhầm. Vì vậy model chỉ là tín hiệu phân tích, chưa phù hợp tự động ra quyết định.

## Tài liệu

- `artifacts/data_contract_us_accidents.md`: hợp đồng dữ liệu và quy tắc đánh giá.
- `docs/muc_3_tong_hop_lien_ky_thuat.md`: nội dung kỹ thuật cho Mục 3 báo cáo.
- `docs/nhat_ky_quyet_dinh.md`: quyết định, bằng chứng và phương án không chọn.

Mọi kết quả là liên hệ quan sát trong snapshot CA/TX, không chứng minh quan hệ nhân quả hoặc thương vong.
