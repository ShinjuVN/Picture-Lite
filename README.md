# 🖼 Software Picture Lite

Ứng dụng Desktop **mã nguồn mở**, giao diện nhẹ và đẹp, giúp nén ảnh (PNG, JPG, JPEG, WEBP) nhanh chóng — hỗ trợ nén đơn lẻ và nén hàng loạt cả một cây thư mục.

Xây dựng bằng **Python + CustomTkinter + Pillow** (100% thư viện miễn phí, mã nguồn mở).

---

## 1. Tính năng chính

| Tính năng | Mô tả |
|---|---|
| ⚙️ Cài đặt | Tuỳ chỉnh đường dẫn lưu mặc định (mặc định: `Downloads`) và mức chất lượng nén. Lưu tại `config/settings.json`. |
| 🖼 Nén ảnh đơn | Chọn 1 ảnh → tự động lưu vào thư mục mặc định với tên `ten_goc_compress.dinh_dang`. |
| 🗂 Nén hàng loạt (nhiều file) | Chọn nhiều ảnh rời → nén & xuất toàn bộ ra thư mục lưu mặc định. |
| 📂 Nén hàng loạt (thư mục) | Quét đệ quy toàn bộ cây thư mục, tự động **bỏ qua** ảnh đã nén hoặc không giảm dung lượng đáng kể, và **thay thế trực tiếp** file gốc (backup gốc thành `ten_goc_old.dinh_dang`). |
| 📋 Log tiến trình | Hiển thị tiến trình dạng console theo thời gian thực, không làm treo giao diện (đa luồng). |

---

## 📌 Bạn muốn làm gì?

Chọn hướng dẫn phù hợp với nhu cầu của bạn:

- 👉 **[Mục 1 — Tôi chỉ muốn cài đặt và sử dụng phần mềm](#mục-1--hướng-dẫn-cài-đặt-phần-mềm-dành-cho-người-dùng)**
  *(Tải và chạy file `setup Picture Lite.exe`, không cần biết lập trình)*
- 👉 **[Mục 2 — Tôi muốn mày mò / chỉnh sửa / đóng góp mã nguồn Python](#mục-2--hướng-dẫn-cài-đặt-từ-mã-nguồn-python-dành-cho-nhà-phát-triển)**
  *(Chạy trực tiếp từ source code, dành cho lập trình viên)*

---

## Mục 1 — Hướng dẫn cài đặt phần mềm (Dành cho người dùng)

Nếu bạn chỉ muốn cài phần mềm để sử dụng ngay mà không cần quan tâm đến mã nguồn Python:

1. Truy cập vào mục **[Releases](../../releases)** của dự án trên GitHub.
2. Tải về file cài đặt mới nhất: **`setup Picture Lite.exe`** (hoặc bản Portable **`Picture-Lite-Portable.exe`** nếu không muốn cài đặt).
3. Mở file `setup Picture Lite.exe` vừa tải về, làm theo các bước hướng dẫn trên màn hình cài đặt (chọn đường dẫn cài đặt, bấm *Next*).
4. Sau khi hoàn tất, bạn có thể khởi chạy ứng dụng trực tiếp từ **Shortcut ngoài Desktop** hoặc trong Menu Start.

📎 Xem thêm **[4. Hướng dẫn sử dụng nhanh](#4-hướng-dẫn-sử-dụng-nhanh)** bên dưới để biết cách dùng các tính năng nén ảnh sau khi cài đặt xong.

---

## Mục 2 — Hướng dẫn cài đặt từ mã nguồn Python (Dành cho nhà phát triển)

Dành cho những ai muốn tự mày mò, tùy biến hoặc đóng góp mã nguồn cho dự án.

### 2.1. Cấu trúc dự án

```
SoftwarePictureLite/
├── assets/                     # Icon và hình ảnh giao diện
│   └── icon.png
├── config/                     # File cấu hình
│   └── settings.json
├── core/                       # Logic xử lý (không phụ thuộc giao diện)
│   ├── __init__.py
│   ├── settings_manager.py     # Đọc/ghi settings.json
│   ├── compressor.py           # Logic nén ảnh cấp thấp (Pillow)
│   ├── file_utils.py           # Quét thư mục, đặt tên file, định dạng dung lượng
│   └── batch_processor.py      # Điều phối nén hàng loạt (file rời / thư mục)
├── gui/                         # Giao diện người dùng (CustomTkinter)
│   ├── __init__.py
│   ├── main_window.py          # Cửa sổ chính, ghép các tab + log
│   ├── log_widget.py           # Bảng log/tiến trình
│   ├── single_compress_frame.py
│   ├── batch_compress_frame.py
│   └── settings_frame.py
├── main.py                     # File chạy chính
├── requirements.txt
└── README.md
```

**Nguyên tắc kiến trúc:** `core/` xử lý toàn bộ logic (nén ảnh, quét file, cấu hình) và **không hề import bất kỳ thứ gì từ `gui/`**. Điều này giúp logic dễ kiểm thử độc lập (unit test) và dễ tái sử dụng nếu sau này muốn đổi giao diện.

### 2.2. Cài đặt & chạy ứng dụng từ mã nguồn

#### Bước 1 — Cài Python

Cần **Python 3.9 trở lên**. Kiểm tra bằng lệnh:

```bash
python3 --version
```

#### Bước 2 — Tải mã nguồn và cài thư viện

```bash
# Di chuyển vào thư mục dự án
cd SoftwarePictureLite

# (Khuyến nghị) Tạo môi trường ảo
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Cài các thư viện cần thiết
pip install -r requirements.txt
```

> Trên Linux, nếu gặp lỗi `ModuleNotFoundError: No module named 'tkinter'`, cần cài thêm gói hệ thống:
> ```bash
> sudo apt-get install python3-tk
> ```

#### Bước 3 — Chạy ứng dụng

```bash
python main.py
```

Ứng dụng sẽ tự động tạo file `config/settings.json` (nếu chưa có) với đường dẫn lưu mặc định là thư mục `Downloads` của bạn.

---

## 4. Hướng dẫn sử dụng nhanh

1. **Tab Cài đặt** — chọn thư mục lưu ảnh nén, chọn mức chất lượng (khuyến nghị 75–90), bấm **Lưu cài đặt**.
2. **Tab Nén ảnh đơn** — bấm **Chọn ảnh...**, chọn 1 file, bấm **Nén ảnh**. Kết quả nằm trong thư mục lưu mặc định, tên dạng `ten_goc_compress.png`.
3. **Tab Nén hàng loạt**:
   - **Chọn nhiều ảnh...** → chọn nhiều file cùng lúc → **Bắt đầu nén** → toàn bộ ảnh nén sẽ xuất ra thư mục lưu mặc định.
   - **Chọn thư mục...** → chọn thư mục gốc (ví dụ thư mục source code) → **Bắt đầu nén** → ứng dụng quét toàn bộ thư mục con, nén và **thay thế trực tiếp từng ảnh gốc**, đồng thời giữ lại bản gốc với tên `ten_goc_old.png` phòng khi cần khôi phục.
4. Theo dõi tiến trình ở khung **Nhật ký tiến trình** bên phải:

```
</> anh1.png [45%]
</> Đã lưu anh1.png về đường dẫn: /home/user/Downloads/anh1_compress.png
</> anh2.png bỏ qua | Lý do: Đã nén
</> Completed
```

### Cơ chế bỏ qua thông minh (chỉ áp dụng khi quét thư mục)

- Nếu tồn tại file `ten_goc_old.dinh_dang` cùng thư mục → coi như ảnh đã được nén ở lần chạy trước → **bỏ qua** (lý do: "Đã nén").
- Nếu nén thử mà dung lượng mới không nhỏ hơn bản gốc ít nhất **5%** → **bỏ qua** (lý do: "Kích thước không giảm đáng kể"), không thay thế gì cả.
- Chỉ khi nén thực sự hiệu quả, ứng dụng mới đổi tên file gốc thành `_old` và đưa file nén mới vào đúng vị trí/tên ban đầu.

---

## 5. Đóng gói thành file .exe / ứng dụng độc lập (tuỳ chọn)

Nếu muốn đóng gói thành file thực thi không cần cài Python, có thể dùng [PyInstaller](https://pyinstaller.org/) (cài thêm qua `pip install pyinstaller`):

```bash
pyinstaller PictureLite.spec
```

---

## 6. Giấy phép

Dự án sử dụng hoàn toàn các thư viện mã nguồn mở, miễn phí:

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (MIT License)
- [Pillow](https://python-pillow.org/) (HPND License)

Bạn có thể tự do sử dụng, chỉnh sửa và phân phối lại mã nguồn này.