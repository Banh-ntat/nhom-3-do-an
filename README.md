# Đồ án Khai phá dữ liệu — Nhận diện và diễn giải các tổ hợp điều kiện liên quan đến mức độ nghiêm trọng của tai nạn giao thông (US Accidents)

## 1. Cấu trúc thư mục

```text
ten-nhom-do-an/
|-- README.md                       # File này: cách chạy lại, môi trường
|-- requirements.txt                # Danh sách thư viện và phiên bản (bao gồm imbalanced-learn)
|-- data/                           # Dẫn tới bộ dữ liệu đã dùng ở bài tập (hoặc script tải)
|   `-- accidents_preprocessed.csv  # Nguồn duy nhất cho notebook tổng hợp (có cột ID)
|-- artifacts/                      # Sản phẩm trung gian tái lập được (split, rules, predictions...)
|-- docs/                           # data_contract, nhật ký quyết định, phiếu đề xuất
|-- phan-tich-tong-hop.ipynb        # Notebook tổng hợp liên kỹ thuật + toàn bộ hình/bảng cho báo cáo
`-- report/
    `-- bao-cao.pdf                 # Báo cáo cuối, đúng khung Phụ lục A của đề
```

## 2. Môi trường chạy lại

- Python phiên bản: `……` (ghi rõ theo `artifacts/environment.lock.txt`)
- Cài đặt thư viện:

```bash
pip install -r requirements.txt
```

- Thư viện bắt buộc có trong `requirements.txt`: `pandas`, `numpy`, `scikit-learn`, `mlxtend` (hoặc thư viện luật kết hợp đang dùng), `imbalanced-learn` (cho Balanced Random Forest), `matplotlib`/`seaborn`.

## 3. Cách chạy lại notebook tổng hợp

1. Đặt `accidents_preprocessed.csv` vào thư mục `data/` (đường dẫn tương đối, không dùng đường dẫn tuyệt đối cá nhân).
2. Khởi động kernel sạch (Restart Kernel).
3. Chạy `Run All` trên `phan-tich-tong-hop.ipynb` từ đầu đến cuối, không cần thao tác thủ công giữa các cell.
4. Notebook sẽ tự tạo lại theo đúng thứ tự: data contract → split chung theo `ID` → tái tạo phân lớp → tái tạo luật kết hợp → kiểm tra rule trên test → phân tích lỗi/độ bền → Balanced Random Forest → toàn bộ bảng/hình dùng trong `report/bao-cao.pdf`.
5. Mọi bảng/hình xuất hiện trong báo cáo phải khớp với output sinh ra từ lần chạy này (không dùng số liệu chỉnh tay).

## 4. Seed và khả năng tái lập

- `random_state = 42` cho toàn bộ train/test split (`StratifiedShuffleSplit`) và các bước có yếu tố ngẫu nhiên (tuning, bootstrap).
- Không fit bất kỳ bước biến đổi nào (impute, scale, discretize, mô hình, frequent-itemsets) trên tập test.
- Mọi liên kết giữa các bảng dùng khóa `ID`, không ghép theo vị trí dòng.

## 5. Ghi chú liêm chính học thuật

- Khai báo sử dụng công cụ AI: xem Phụ lục B trong `report/bao-cao.pdf`.
- Nhật ký quyết định: xem `docs/nhat_ky_quyet_dinh.md`.
- Tài liệu tham khảo trích dẫn theo chuẩn IEEE trong báo cáo.