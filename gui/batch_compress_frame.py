"""
gui/batch_compress_frame.py
------------------------------
Giao diện tab "Nén hàng loạt":
    - Chọn NHIỀU FILE ảnh rời -> nén & xuất ra thư mục lưu mặc định (Cài đặt).
    - Chọn 1 THƯ MỤC -> quét đệ quy toàn bộ cây thư mục, tự động bỏ qua ảnh
      đã nén / không nén được đáng kể, và thay thế trực tiếp file gốc.
"""

import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.settings_manager import load_settings
from core.batch_processor import compress_file_list, compress_directory


class BatchCompressFrame(ctk.CTkFrame):
    def __init__(self, master, emit_event, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.emit_event = emit_event
        self.selected_files = []
        self.selected_directory = None
        self._build_ui()

    def _build_ui(self) -> None:
        title = ctk.CTkLabel(self, text="🗂  Nén ảnh hàng loạt", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(anchor="w", padx=20, pady=(20, 6))

        desc = ctk.CTkLabel(
            self,
            text=(
                "•  Chọn nhiều ảnh: nén và xuất toàn bộ ra thư mục lưu (xem tab Cài đặt).\n"
                "•  Chọn thư mục: quét toàn bộ cây thư mục con, tự động bỏ qua ảnh đã nén\n"
                "   hoặc không nén được đáng kể, và THAY THẾ trực tiếp file gốc tại chỗ."
            ),
            font=ctk.CTkFont(size=12), text_color="gray", justify="left",
        )
        desc.pack(anchor="w", padx=20, pady=(0, 18))

        self.selection_label = ctk.CTkLabel(
            self, text="Chưa chọn ảnh hoặc thư mục nào.", font=ctk.CTkFont(size=13),
            text_color="gray", anchor="w", wraplength=560, justify="left",
        )
        self.selection_label.pack(fill="x", padx=20, pady=(0, 18))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=20)

        choose_files_btn = ctk.CTkButton(
            btn_row, text="🖼  Chọn nhiều ảnh...", command=self._choose_files, width=170
        )
        choose_files_btn.pack(side="left", padx=(0, 10))

        choose_folder_btn = ctk.CTkButton(
            btn_row, text="📂  Chọn thư mục...", command=self._choose_folder, width=170
        )
        choose_folder_btn.pack(side="left")

        self.start_btn = ctk.CTkButton(
            self, text="🗜  Bắt đầu nén", command=self._start_compress, width=170, height=38,
            fg_color="#2FA572", hover_color="#248A5D",
        )
        self.start_btn.pack(anchor="w", padx=20, pady=(26, 10))

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 5))

    # ------------------------------------------------------------------ #
    def _choose_files(self) -> None:
        files = filedialog.askopenfilenames(
            title="Chọn nhiều ảnh cần nén",
            filetypes=[("Ảnh hỗ trợ", "*.png *.jpg *.jpeg *.webp")],
        )
        if files:
            self.selected_files = list(files)
            self.selected_directory = None
            self.selection_label.configure(
                text=f"Đã chọn {len(self.selected_files)} ảnh (sẽ xuất ra thư mục lưu mặc định).",
                text_color="white",
            )

    def _choose_folder(self) -> None:
        folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh cần nén")
        if folder:
            self.selected_directory = folder
            self.selected_files = []
            self.selection_label.configure(
                text=f"Đã chọn thư mục: {folder}\n(sẽ quét toàn bộ cây thư mục & thay thế file gốc)",
                text_color="white",
            )

    def set_running_state(self, is_running: bool) -> None:
        """Bật/tắt trạng thái nút bấm + thanh tiến trình (gọi từ main_window)."""
        if is_running:
            self.start_btn.configure(state="disabled", text="Đang xử lý...")
            self.progress_bar.configure(mode="indeterminate")
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(1)
            self.start_btn.configure(state="normal", text="🗜  Bắt đầu nén")

    def _start_compress(self) -> None:
        if not self.selected_files and not self.selected_directory:
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất 1 ảnh hoặc 1 thư mục trước khi bắt đầu.")
            return

        self.emit_event("batch_ui_state", True)
        threading.Thread(target=self._batch_worker, daemon=True).start()

    def _batch_worker(self) -> None:
        """Chạy toàn bộ luồng xử lý nén hàng loạt trên background thread."""
        settings = load_settings()
        quality = settings.get("quality", 85)

        if self.selected_directory:
            compress_directory(self.selected_directory, quality, self.emit_event)
        else:
            save_dir = settings.get("save_path")
            compress_file_list(self.selected_files, save_dir, quality, self.emit_event)

        self.emit_event("batch_ui_state", False)
