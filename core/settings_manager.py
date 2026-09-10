"""
core/settings_manager.py
-------------------------
Quản lý việc đọc/ghi cấu hình ứng dụng từ file config/settings.json.

File cấu hình lưu các thông tin:
    - save_path          : Thư mục lưu ảnh sau khi nén (mặc định: Downloads)
    - quality             : Mức chất lượng nén ảnh (1 - 100)
    - theme                : Giao diện sáng / tối (light / dark)
    - keep_old_backup      : Khi quét thư mục để nén, có giữ lại ảnh gốc hay không
    - backup_to_temp_cache : Nếu giữ lại ảnh gốc, lưu vào thư mục tạm hệ thống
                              thay vì lưu ngay cạnh ảnh với hậu tố "_old"
    - temp_cache_dir       : Đường dẫn thư mục cache tạm (được dò tìm 1 lần duy
                              nhất ở lần chạy đầu tiên dựa trên %TEMP% của máy,
                              sau đó lưu cố định vào settings.json để dùng lại)
"""

import os
import sys
import json
import tempfile

# BASE_DIR = thư mục gốc chứa file cấu hình.
#   - Khi chạy trực tiếp bằng "python main.py": là thư mục gốc dự án
#     (thư mục chứa main.py), tức thư mục CHA của core/.
#   - Khi đã đóng gói bằng PyInstaller (--onedir): __file__ của module này
#     KHÔNG còn nằm cạnh main.py nữa mà bị PyInstaller bung vào trong
#     "_internal/core/settings_manager.py". Vì vậy phải dùng
#     os.path.dirname(sys.executable) để lấy đúng thư mục chứa PictureLite.exe
#     (nơi bạn đặt thư mục "config/" cạnh file .exe), thay vì dựa vào __file__.
#     PyInstaller tự gắn cờ sys.frozen = True khi chạy dưới dạng .exe đã đóng gói.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_DIR = os.path.join(BASE_DIR, "config")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")


def _detect_default_temp_cache_dir() -> str:
    """
    Dò đường dẫn thư mục tạm (%TEMP% trên Windows, /tmp trên Linux/macOS)
    của MÁY HIỆN TẠI, rồi tạo thư mục con "Picture-Lite" bên trong đó.
    Hàm này chỉ nên được gọi 1 lần (khi settings.json chưa có key này),
    kết quả sẽ được lưu cố định vào settings.json cho các lần chạy sau.
    """
    return os.path.join(tempfile.gettempdir(), "Picture-Lite")


# Cấu hình mặc định khi ứng dụng chạy lần đầu tiên
DEFAULT_SETTINGS = {
    "save_path": os.path.join(os.path.expanduser("~"), "Downloads"),
    "quality": 85,
    "theme": "dark",
    "keep_old_backup": True,
    "backup_to_temp_cache": False,
    "temp_cache_dir": _detect_default_temp_cache_dir(),
}


def load_settings() -> dict:
    """
    Đọc cấu hình từ file config/settings.json.
    Nếu file chưa tồn tại hoặc bị lỗi định dạng, tự động tạo lại file
    với cấu hình mặc định. Nếu file đã tồn tại nhưng thiếu key mới
    (do nâng cấp phiên bản), tự động bổ sung và LƯU LẠI ngay để các
    lần chạy sau đọc thẳng từ file thay vì dò lại.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)

    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)

        # Bổ sung các key còn thiếu (phòng trường hợp nâng cấp phiên bản mới),
        # và ghi lại file ngay nếu có bổ sung để "chốt" giá trị dò được.
        needs_save = False
        for key, value in DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = value
                needs_save = True

        # Luôn giải mã ký tự "~" thành đường dẫn thư mục home thật của hệ điều hành
        settings["save_path"] = os.path.expanduser(settings.get("save_path", ""))

        if needs_save:
            save_settings(settings)

        return settings
    except (json.JSONDecodeError, OSError):
        # File hỏng -> khôi phục cấu hình mặc định
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()


def save_settings(settings: dict) -> None:
    """Ghi cấu hình hiện tại ra file config/settings.json."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)