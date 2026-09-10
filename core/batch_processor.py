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
    build_temp_cache_backup_path,
    has_temp_cache_backup,
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


def compress_directory(
    directory: str,
    quality: int,
    emit_event,
    keep_old_backup: bool = True,
    backup_to_temp: bool = False,
    temp_cache_dir: str = "",
) -> None:
    """
    Quét toàn bộ cây thư mục để tìm ảnh hợp lệ, sau đó với mỗi ảnh xử lý
    theo 1 trong 3 chế độ, tuỳ vào 2 tham số keep_old_backup / backup_to_temp:

    ┌─────────────────┬──────────────────┬────────────────────────────────────┐
    │ keep_old_backup │ backup_to_temp   │ Hành vi                             │
    ├─────────────────┼──────────────────┼────────────────────────────────────┤
    │ False           │ (bỏ qua)         │ Ghi đè thẳng ảnh gốc, KHÔNG backup. │
    │ True            │ False            │ Đổi tên gốc -> "<ten>_old.<ext>"    │
    │                 │                  │ cùng thư mục (hành vi phiên bản 1). │
    │ True            │ True             │ Chuyển ảnh gốc (giữ nguyên tên) vào │
    │                 │                  │ temp_cache_dir, mirror lại cấu trúc │
    │                 │                  │ thư mục để tránh trùng tên.         │
    └─────────────────┴──────────────────┴────────────────────────────────────┘

    Trong mọi chế độ, ảnh vẫn bị bỏ qua nếu:
      - Phát hiện đã có bản backup của nó từ trước (chỉ áp dụng khi
        keep_old_backup=True, vì đây là cách duy nhất còn "dấu vết" để nhận biết).
      - Nén thử mà dung lượng mới không nhỏ hơn bản gốc ít nhất 5%.
    """
    image_files = scan_images_in_directory(directory)

    if not image_files:
        emit_event("info", "Không tìm thấy ảnh hợp lệ (png/jpg/jpeg/webp) trong thư mục đã chọn.")
        emit_event("completed")
        return

    for file_path in image_files:
        filename = os.path.basename(file_path)

        # Bước 1: Bỏ qua nếu ảnh đã từng được nén trước đó.
        # Chỉ kiểm tra được khi có bật giữ backup (vì cần "dấu vết" để nhận biết).
        if keep_old_backup:
            already_done = (
                has_temp_cache_backup(file_path, temp_cache_dir)
                if backup_to_temp
                else has_old_backup(file_path)
            )
            if already_done:
                emit_event("skip", filename, "Đã nén")
                continue

        emit_event("progress", filename, 15)

        # Bước 2: Nén thử ra file tạm cùng thư mục để so sánh dung lượng.
        # Giữ nguyên phần đuôi mở rộng (.png/.jpg/.webp) trong tên file tạm để
        # compress_image_to_path() nhận diện đúng định dạng cần lưu.
        file_dir = os.path.dirname(file_path)
        name, ext = os.path.splitext(filename)
        temp_output_path = os.path.join(file_dir, f".tmp_{name}{ext}")
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

        # Bước 3: Thay thế ảnh gốc theo đúng chế độ backup đã chọn
        try:
            if not keep_old_backup:
                # Không giữ bản gốc -> ghi đè thẳng
                os.replace(temp_output_path, file_path)
            elif backup_to_temp:
                # Giữ bản gốc trong thư mục cache tạm (giữ nguyên tên file)
                backup_path = build_temp_cache_backup_path(file_path, temp_cache_dir)
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                os.replace(file_path, backup_path)
                os.replace(temp_output_path, file_path)
            else:
                # Giữ bản gốc ngay cạnh, đổi tên thành "<ten>_old.<ext>"
                old_backup_path = build_old_backup_path(file_path)
                os.replace(file_path, old_backup_path)
                os.replace(temp_output_path, file_path)
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
