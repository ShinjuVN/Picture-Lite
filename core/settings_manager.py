"""
core/settings_manager.py
-------------------------
Quản lý việc đọc/ghi cấu hình ứng dụng từ file config/settings.json.

File cấu hình lưu các thông tin:
    - save_path : Đường dẫn thư mục lưu ảnh sau khi nén (mặc định: Downloads)
    - quality   : Mức chất lượng nén ảnh (1 - 100)
    - theme     : Giao diện sáng / tối (light / dark)
"""

import os
import json

# BASE_DIR = thư mục gốc của dự án (thư mục chứa main.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")

# Cấu hình mặc định khi ứng dụng chạy lần đầu tiên
DEFAULT_SETTINGS = {
    "save_path": os.path.join(os.path.expanduser("~"), "Downloads"),
    "quality": 85,
    "theme": "dark",
}


def load_settings() -> dict:
    """
    Đọc cấu hình từ file config/settings.json.
    Nếu file chưa tồn tại hoặc bị lỗi định dạng, tự động tạo lại file
    với cấu hình mặc định.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)

    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        # Bổ sung các key còn thiếu (phòng trường hợp nâng cấp phiên bản mới)
        for key, value in DEFAULT_SETTINGS.items():
            settings.setdefault(key, value)
        # Luôn giải mã ký tự "~" thành đường dẫn thư mục home thật của hệ điều hành
        # (cho phép file settings.json mẫu dùng "~/Downloads" trên mọi máy)
        settings["save_path"] = os.path.expanduser(settings.get("save_path", ""))
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
