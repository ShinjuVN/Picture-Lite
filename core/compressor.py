"""
core/compressor.py
-------------------
Chứa toàn bộ logic nén ảnh cấp thấp, sử dụng thư viện Pillow.
Module này KHÔNG biết gì về giao diện hay luồng xử lý — chỉ thuần
xử lý ảnh, để có thể tái sử dụng ở bất kỳ đâu (đơn lẻ, hàng loạt, test...).
"""

import os
from PIL import Image

# Các định dạng ảnh chuẩn được ứng dụng hỗ trợ nén
SUPPORTED_FORMATS = (".png", ".jpg", ".jpeg", ".webp")

# Ngưỡng phần trăm giảm dung lượng tối thiểu để coi là "nén có hiệu quả".
# Dưới ngưỡng này, ảnh sẽ được coi là không đáng để thay thế bản gốc.
MIN_REDUCTION_PERCENT = 5.0


def is_supported_image(file_path: str) -> bool:
    """Kiểm tra file có phải là định dạng ảnh được hỗ trợ hay không."""
    return file_path.lower().endswith(SUPPORTED_FORMATS)


def get_file_size(file_path: str) -> int:
    """Trả về dung lượng file theo byte. Trả về 0 nếu file không tồn tại."""
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0


def compress_image_to_path(input_path: str, output_path: str, quality: int) -> bool:
    """
    Nén ảnh từ input_path và lưu kết quả ra output_path theo mức quality (1-100).

    - JPG/JPEG: dùng tham số quality trực tiếp, tự convert sang RGB nếu ảnh có alpha.
    - PNG     : PNG là định dạng nén không mất dữ liệu (lossless), quality được quy
                đổi sang compress_level (0-9) của Pillow để tối ưu dung lượng.
    - WEBP    : dùng tham số quality trực tiếp cùng method=6 (nén kỹ nhất).

    Trả về True nếu nén + lưu thành công, False nếu có lỗi xảy ra.
    """
    try:
        with Image.open(input_path) as img:
            ext = os.path.splitext(output_path)[1].lower()

            if ext in (".jpg", ".jpeg"):
                # JPEG không hỗ trợ kênh alpha -> convert về RGB trước khi lưu
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                img.save(output_path, "JPEG", quality=int(quality), optimize=True)

            elif ext == ".png":
                # Quy đổi quality (1-100) -> compress_level (9-0): quality càng cao,
                # compress_level càng thấp (ưu tiên tốc độ / giữ nguyên chất lượng).
                compress_level = min(9, max(0, int(9 - (quality / 100) * 9)))
                img.save(output_path, "PNG", optimize=True, compress_level=compress_level)

            elif ext == ".webp":
                img.save(output_path, "WEBP", quality=int(quality), method=6)

            else:
                img.save(output_path, quality=int(quality), optimize=True)

        return True

    except Exception as error:  # noqa: BLE001 - cần bắt mọi lỗi ảnh hỏng/không đọc được
        print(f"[Lỗi nén ảnh] {input_path}: {error}")
        return False


def is_significant_reduction(original_size: int, new_size: int,
                              min_percent: float = MIN_REDUCTION_PERCENT) -> bool:
    """
    Kiểm tra dung lượng sau khi nén có giảm 'đáng kể' so với bản gốc hay không,
    dựa trên ngưỡng phần trăm tối thiểu (mặc định 5%).
    """
    if original_size <= 0:
        return False
    reduction_percent = (original_size - new_size) / original_size * 100
    return reduction_percent >= min_percent


def has_old_backup(file_path: str) -> bool:
    """
    Kiểm tra xem ảnh này đã từng được nén (thay thế tại chỗ) trước đó hay chưa.
    Cơ chế nhận diện: mỗi lần nén thư mục, ứng dụng luôn tạo file backup
    dạng "<ten>_old.<ext>" cùng thư mục. Nếu file này đã tồn tại thì có
    nghĩa là ảnh hiện tại chính là kết quả của lần nén trước đó.
    """
    directory = os.path.dirname(file_path)
    name, ext = os.path.splitext(os.path.basename(file_path))
    old_file = os.path.join(directory, f"{name}_old{ext}")
    return os.path.exists(old_file)
