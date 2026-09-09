"""
core/file_utils.py
-------------------
Các hàm tiện ích thao tác với file/thư mục: quét cây thư mục tìm ảnh,
tạo tên file đầu ra, định dạng dung lượng hiển thị, v.v.
"""

import os
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
