# Quick Meet Link

<p align="center">
  <img src="img/logo-app.png" alt="Quick Meet Link logo" width="120" />
</p>

<p align="center">
  Ứng dụng desktop (Tkinter) giúp mở hàng loạt link <strong>Google Meet</strong> bằng đúng trình duyệt bạn chọn chỉ với vài thao tác.
</p>

## ✨ Tính năng chính

- Dán nhiều link cùng lúc (mỗi dòng một link hoặc cả khối văn bản).
- Tự động tách URL từ nội dung đã dán.
- Tự động quét các trình duyệt đã cài trên Windows.
- Ưu tiên nhận diện trình duyệt mặc định của hệ thống.
- Giao diện trực quan, có logo từng trình duyệt để chọn nhanh.

## 🖼️ Tài nguyên hình ảnh

Dự án có sẵn bộ ảnh logo trong thư mục [`img/`](img):

- `logo-app.png`
- `chrome.png`
- `edge.png`
- `firefox.png`
- `brave.png`
- `opera.png`
- `opera_gx.png`
- `vivaldi.png`
- `coccoc.png`

## 🧱 Công nghệ sử dụng

- **Python 3**
- **Tkinter** (GUI)
- **Pillow** (xử lý ảnh)
- **PyInstaller** (đóng gói `.exe`)

## 📦 Cấu trúc thư mục

```text
.
├── app.py                  # Giao diện và luồng xử lý chính
├── check_browser.py        # Phát hiện trình duyệt cài trong máy (Windows)
├── img/                    # Logo ứng dụng + logo trình duyệt
├── Quick meet link.spec    # Cấu hình build bằng PyInstaller
└── dist/                   # File build đầu ra (.exe)
```

## 🚀 Chạy dự án ở chế độ dev

> Yêu cầu: Python 3.10+ (khuyến nghị), hệ điều hành Windows.

1. Tạo môi trường ảo (tuỳ chọn):

```bash
python -m venv .venv
.venv\Scripts\activate
```

2. Cài thư viện:

```bash
pip install pillow cairosvg
```

3. Chạy ứng dụng:

```bash
python app.py
```

## 🏗️ Build file `.exe`

Dự án đã có sẵn file spec. Build bằng lệnh:

```bash
pyinstaller "Quick meet link.spec"
```

Sau khi build, file chạy sẽ nằm trong thư mục `dist/`.

## 🧠 Cách sử dụng nhanh

1. Mở ứng dụng.
2. Dán danh sách link Google Meet vào khung nhập liệu.
3. Chọn trình duyệt từ danh sách đã phát hiện.
4. Bấm nút mở link để mở toàn bộ phòng họp.

## ⚠️ Lưu ý

- Ứng dụng được tối ưu cho **Windows** vì có dùng `winreg` để đọc registry.
- Nên kiểm tra kỹ link trước khi mở hàng loạt.
- Nếu máy chưa cài trình duyệt được hỗ trợ, danh sách trình duyệt sẽ trống.

## 👤 Tác giả

- **Ngọc Trinh**
