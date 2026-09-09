"""
core/batch_processor.py
--------------------------
Điều phối logic nén ảnh HÀNG LOẠT. Đây là lớp "nghiệp vụ" nằm giữa core
và gui: nhận vào danh sách file / thư mục, gọi core.compressor để xử lý
từng ảnh, và phát ra sự kiện (emit_event) để giao diện cập nhật log.

emit_event(event_type: str, *args) được gui truyền vào, cho phép module
này chạy hoàn toàn độc lập với Tkinter/CustomTkinter (dễ test, dễ tái sử dụng).

Các event_type được phát ra:
    "progress" (filename, percent)
    "success"  (filename, save_path)
    "skip"     (filename, reason)
    "info"     (message)
    "completed" ()
"""

import os

from core.compressor import (
    compress_image_to_path,
    get_file_size,
    is_significant_reduction,
    has_old_backup,
)
from core.file_utils import (
    scan_images_in_directory,
    build_output_path_in_folder,
    build_old_backup_path,
    format_size,
)


def compress_file_list(file_list: list, save_dir: str, quality: int, emit_event) -> None:
    """
    Nén một danh sách file ảnh RỜI (do người dùng chọn qua hộp thoại chọn
    nhiều file) và xuất toàn bộ kết quả ra thư mục lưu mặc định (save_dir),
    với tên dạng: ten_goc_compress.dinh_dang
    """
    for file_path in file_list:
        filename = os.path.basename(file_path)

        if not os.path.exists(file_path):
            emit_event("skip", filename, "File không tồn tại")
            continue

        emit_event("progress", filename, 20)
        output_path = build_output_path_in_folder(file_path, save_dir, suffix="_compress")

        emit_event("progress", filename, 60)
        success = compress_image_to_path(file_path, output_path, quality)

        if success:
            emit_event("progress", filename, 100)
            emit_event("success", filename, output_path)
        else:
            emit_event("skip", filename, "Lỗi xử lý ảnh, vui lòng thử lại")

    emit_event("completed")


def compress_directory(directory: str, quality: int, emit_event) -> None:
    """
    Quét toàn bộ cây thư mục để tìm ảnh hợp lệ, sau đó với mỗi ảnh:

    1. Nếu ảnh đã từng được nén trước đó (tồn tại file "<ten>_old.<ext>")
       -> bỏ qua, lý do "Đã nén".
    2. Nén thử ra 1 file tạm để so sánh dung lượng. Nếu dung lượng mới
       không nhỏ hơn đáng kể so với bản gốc -> bỏ qua, xoá file tạm.
    3. Nếu nén hiệu quả: đổi tên file gốc thành "<ten>_old.<ext>" (backup),
       rồi đưa file nén mới vào đúng vị trí & tên ban đầu (thay thế gốc).
    """
    image_files = scan_images_in_directory(directory)

    if not image_files:
        emit_event("info", "Không tìm thấy ảnh hợp lệ (png/jpg/jpeg/webp) trong thư mục đã chọn.")
        emit_event("completed")
        return

    for file_path in image_files:
        filename = os.path.basename(file_path)

        # Bước 1: Bỏ qua nếu ảnh đã từng được nén trước đó
        if has_old_backup(file_path):
            emit_event("skip", filename, "Đã nén")
            continue

        emit_event("progress", filename, 15)

        # Bước 2: Nén thử ra file tạm cùng thư mục để so sánh dung lượng.
        # Giữ nguyên phần đuôi mở rộng (.png/.jpg/.webp) trong tên file tạm để
        # compress_image_to_path() nhận diện đúng định dạng cần lưu.
        directory = os.path.dirname(file_path)
        name, ext = os.path.splitext(filename)
        temp_output_path = os.path.join(directory, f".tmp_{name}{ext}")
        emit_event("progress", filename, 50)

        success = compress_image_to_path(file_path, temp_output_path, quality)
        if not success:
            emit_event("skip", filename, "Lỗi xử lý ảnh")
            _safe_remove(temp_output_path)
            continue

        original_size = get_file_size(file_path)
        new_size = get_file_size(temp_output_path)

        if not is_significant_reduction(original_size, new_size):
            emit_event(
                "skip", filename,
                f"Kích thước không giảm đáng kể ({format_size(original_size)} → {format_size(new_size)})",
            )
            _safe_remove(temp_output_path)
            continue

        emit_event("progress", filename, 85)

        # Bước 3: Backup file gốc rồi thay thế bằng bản nén mới
        old_backup_path = build_old_backup_path(file_path)
        try:
            os.rename(file_path, old_backup_path)
            os.rename(temp_output_path, file_path)
        except OSError as error:
            emit_event("skip", filename, f"Lỗi khi thay thế file: {error}")
            _safe_remove(temp_output_path)
            continue

        emit_event("progress", filename, 100)
        emit_event("success", filename, file_path)

    emit_event("completed")


def _safe_remove(path: str) -> None:
    """Xoá file tạm một cách an toàn, không phát sinh lỗi nếu file không tồn tại."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
