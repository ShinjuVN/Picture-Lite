"""
core/file_utils.py
-------------------
Các hàm tiện ích thao tác với file/thư mục: quét cây thư mục tìm ảnh,
tạo tên file đầu ra, định dạng dung lượng hiển thị, quản lý backup
trong thư mục cache tạm, và mở thư mục bằng trình quản lý file hệ điều hành.
"""

import os
import sys
import subprocess
from core.compressor import SUPPORTED_FORMATS


def is_backup_file(file_path: str) -> bool:
    """
    Kiểm tra file có phải là bản backup do chính ứng dụng tạo ra hay không
    (dạng "<ten>_old.<ext>"). Các file này không được coi là ảnh cần xử lý,
    nếu không ứng dụng sẽ tự nén lại chính các bản backup của nó.
    """
    name, _ext = os.path.splitext(os.path.basename(file_path))
    return name.endswith("_old")


def scan_images_in_directory(directory: str) -> list:
    """
    Quét đệ quy toàn bộ cây thư mục để tìm các file ảnh có định dạng
    chuẩn (png, jpg, jpeg, webp). Mọi file không phải ảnh sẽ bị bỏ qua,
    cũng như các file backup "<ten>_old.<ext>" do chính ứng dụng tạo ra.

    Trả về danh sách đường dẫn tuyệt đối tới từng file ảnh tìm được.
    """
    image_files = []
    for root, _dirs, files in os.walk(directory):
        for f in files:
            if f.lower().endswith(SUPPORTED_FORMATS) and not is_backup_file(f):
                image_files.append(os.path.join(root, f))
    return image_files


def build_output_path_in_folder(original_path: str, target_folder: str,
                                 suffix: str = "_compress") -> str:
    """
    Tạo đường dẫn file đầu ra bên trong 1 thư mục đích cụ thể (dùng cho
    nén ảnh đơn và nén nhiều file rời), theo định dạng:
        <thu_muc_dich>/<ten_goc><suffix>.<dinh_dang>
    """
    os.makedirs(target_folder, exist_ok=True)
    name, ext = os.path.splitext(os.path.basename(original_path))
    return os.path.join(target_folder, f"{name}{suffix}{ext}")


def build_old_backup_path(original_path: str, suffix: str = "_old") -> str:
    """
    Tạo đường dẫn cho file backup của ảnh gốc (dùng khi quét & thay thế
    trực tiếp trong thư mục), theo định dạng:
        <cung_thu_muc>/<ten_goc><suffix>.<dinh_dang>
    """
    directory = os.path.dirname(original_path)
    name, ext = os.path.splitext(os.path.basename(original_path))
    return os.path.join(directory, f"{name}{suffix}{ext}")


def format_size(size_bytes: int) -> str:
    """Định dạng dung lượng file (byte) sang chuỗi dễ đọc: B, KB hoặc MB."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 ** 2):.2f} MB"


def build_temp_cache_backup_path(original_path: str, temp_cache_dir: str) -> str:
    """
    Tạo đường dẫn backup trong thư mục cache tạm hệ thống, MIRROR lại toàn bộ
    đường dẫn gốc (ổ đĩa + đường dẫn con) để:
        1. Không cần đổi tên thành "_old" (giữ nguyên tên file gốc).
        2. Không bị trùng/ghi đè giữa các ảnh cùng tên ở các thư mục khác nhau.

    Ví dụ trên Windows:
        D:\\Projects\\Game\\ui\\icon.png
        -> <temp_cache_dir>\\D\\Projects\\Game\\ui\\icon.png
    """
    abs_path = os.path.abspath(original_path)
    drive, tail = os.path.splitdrive(abs_path)
    drive_name = drive.replace(":", "") if drive else "root"
    tail = tail.lstrip("\\/")
    # Chuẩn hoá dấu phân cách theo hệ điều hành hiện tại
    tail_parts = tail.replace("\\", "/").split("/")
    return os.path.join(temp_cache_dir, drive_name, *tail_parts)


def has_temp_cache_backup(original_path: str, temp_cache_dir: str) -> bool:
    """Kiểm tra ảnh này đã từng được backup vào thư mục cache tạm hay chưa."""
    backup_path = build_temp_cache_backup_path(original_path, temp_cache_dir)
    return os.path.exists(backup_path)


def open_folder_in_explorer(path: str) -> None:
    """
    Mở 1 thư mục bằng trình quản lý file mặc định của hệ điều hành
    (Explorer trên Windows, Finder trên macOS, hoặc trình quản lý file
    mặc định trên Linux). Tự động tạo thư mục nếu chưa tồn tại.
    """
    os.makedirs(path, exist_ok=True)
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as error:  # noqa: BLE001
        print(f"[Lỗi mở thư mục] {path}: {error}")
