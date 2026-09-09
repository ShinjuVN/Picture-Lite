"""
gui/single_compress_frame.py
-------------------------------
Giao diện tab "Nén ảnh đơn": chọn 1 file ảnh, nén và lưu tự động vào
thư mục mặc định (cấu hình trong tab Cài đặt) với tên ten_goc_compress.dinh_dang.
"""

import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.settings_manager import load_settings
from core.compressor import compress_image_to_path, is_supported_image
from core.file_utils import build_output_path_in_folder


class SingleCompressFrame(ctk.CTkFrame):
    def __init__(self, master, emit_event, **kwargs):
        """
        emit_event: hàm callback (event_type, *args) dùng để gửi sự kiện log
        về main_window một cách an toàn giữa các luồng (thread-safe).
        """
        super().__init__(master, fg_color="transparent", **kwargs)
        self.emit_event = emit_event
        self.selected_file = None
        self._build_ui()

    def _build_ui(self) -> None:
        title = ctk.CTkLabel(self, text="🖼  Nén ảnh đơn", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(anchor="w", padx=20, pady=(20, 6))

        desc = ctk.CTkLabel(
            self,
            text="Chọn 1 ảnh (PNG/JPG/JPEG/WEBP). Ứng dụng sẽ nén và tự động lưu vào\n"
                 "thư mục mặc định với tên dạng: ten_goc_compress.dinh_dang",
            font=ctk.CTkFont(size=12), text_color="gray", justify="left",
        )
        desc.pack(anchor="w", padx=20, pady=(0, 18))

        self.file_label = ctk.CTkLabel(
            self, text="Chưa chọn file ảnh nào.", font=ctk.CTkFont(size=13),
            text_color="gray", anchor="w", justify="left", wraplength=560,
        )
        self.file_label.pack(fill="x", padx=20, pady=(0, 18))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20)

        choose_btn = ctk.CTkButton(btn_row, text="📁  Chọn ảnh...", command=self._choose_file, width=150)
        choose_btn.pack(side="left", padx=(0, 10))

        self.compress_btn = ctk.CTkButton(
            btn_row, text="🗜  Nén ảnh", command=self._start_compress, width=150,
            fg_color="#2FA572", hover_color="#248A5D",
        )
        self.compress_btn.pack(side="left")

    # ------------------------------------------------------------------ #
    def _choose_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh cần nén",
            filetypes=[("Ảnh hỗ trợ", "*.png *.jpg *.jpeg *.webp"), ("Tất cả file", "*.*")],
        )
        if file_path:
            self.selected_file = file_path
            self.file_label.configure(text=f"Đã chọn: {file_path}", text_color="white")

    def set_running_state(self, is_running: bool) -> None:
        """Bật/tắt trạng thái nút bấm khi đang xử lý (gọi từ main_window)."""
        if is_running:
            self.compress_btn.configure(state="disabled", text="Đang nén...")
        else:
            self.compress_btn.configure(state="normal", text="🗜  Nén ảnh")

    def _start_compress(self) -> None:
        if not self.selected_file or not is_supported_image(self.selected_file):
            messagebox.showerror("Lỗi", "Vui lòng chọn 1 file ảnh hợp lệ (png, jpg, jpeg, webp).")
            return
        if not os.path.exists(self.selected_file):
            messagebox.showerror("Lỗi", "File ảnh đã chọn không còn tồn tại.")
            return

        self.emit_event("single_ui_state", True)
        # Chạy nén trong luồng riêng (thread) để không làm treo giao diện chính
        threading.Thread(target=self._compress_worker, daemon=True).start()

    def _compress_worker(self) -> None:
        """Hàm này chạy trên background thread — TUYỆT ĐỐI không thao tác trực
        tiếp lên widget tại đây, mọi cập nhật UI phải đi qua self.emit_event()."""
        settings = load_settings()
        save_dir = settings.get("save_path")
        quality = settings.get("quality", 85)

        filename = os.path.basename(self.selected_file)
        output_path = build_output_path_in_folder(self.selected_file, save_dir, suffix="_compress")

        # Cập nhật tiến trình theo từng bước xử lý (đọc ảnh -> nén -> lưu)
        self.emit_event("progress", filename, 10)
        self.emit_event("progress", filename, 55)

        success = compress_image_to_path(self.selected_file, output_path, quality)

        if success:
            self.emit_event("progress", filename, 100)
            self.emit_event("success", filename, output_path)
        else:
            self.emit_event("skip", filename, "Lỗi xử lý ảnh, vui lòng thử lại")

        self.emit_event("completed")
        self.emit_event("single_ui_state", False)
