"""
gui/batch_compress_frame.py
------------------------------
Giao diện tab "Nén hàng loạt":
    - Chọn NHIỀU FILE ảnh rời -> nén & xuất ra thư mục lưu mặc định (Cài đặt).
    - Chọn 1 THƯ MỤC -> quét đệ quy toàn bộ cây thư mục, tự động bỏ qua ảnh
      đã nén / không nén được đáng kể, và thay thế trực tiếp file gốc.

Riêng chế độ "chọn thư mục" có thêm 2 tuỳ chọn backup ảnh gốc:
    1. "Giữ lại ảnh gốc"      -> bật/tắt việc backup trước khi ghi đè.
    2. "Lưu vào bộ nhớ tạm"    -> nếu bật (và mục 1 cũng đang bật), backup sẽ
       được chuyển vào thư mục cache tạm hệ thống thay vì để cạnh ảnh gốc
       với hậu tố "_old". Đường dẫn cache có thể bấm vào để mở nhanh.
Hai lựa chọn này được lưu ngay vào settings.json mỗi khi người dùng đổi,
để lần mở app sau vẫn giữ nguyên lựa chọn cũ.
"""

import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.settings_manager import load_settings, save_settings
from core.batch_processor import compress_file_list, compress_directory
from core.file_utils import open_folder_in_explorer


class BatchCompressFrame(ctk.CTkFrame):
    def __init__(self, master, emit_event, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.emit_event = emit_event
        self.selected_files = []
        self.selected_directory = None
        self.settings = load_settings()
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
        desc.pack(anchor="w", padx=20, pady=(0, 14))

        self.selection_label = ctk.CTkLabel(
            self, text="Chưa chọn ảnh hoặc thư mục nào.", font=ctk.CTkFont(size=13),
            text_color="gray", anchor="w", wraplength=560, justify="left",
        )
        self.selection_label.pack(fill="x", padx=20, pady=(0, 14))

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

        # ---------------- Tuỳ chọn backup (chỉ áp dụng cho chế độ chọn thư mục) ---------------- #
        backup_box = ctk.CTkFrame(self, corner_radius=10)
        backup_box.pack(fill="x", padx=20, pady=(18, 10))

        backup_title = ctk.CTkLabel(
            backup_box, text="Tuỳ chọn khi quét thư mục", font=ctk.CTkFont(size=13, weight="bold")
        )
        backup_title.pack(anchor="w", padx=14, pady=(12, 4))

        self.keep_old_var = ctk.BooleanVar(value=self.settings.get("keep_old_backup", True))
        self.keep_old_checkbox = ctk.CTkCheckBox(
            backup_box, text="Giữ lại ảnh gốc (bỏ tích: thay thế thẳng, không lưu bản gốc)",
            variable=self.keep_old_var, command=self._on_keep_old_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.keep_old_checkbox.pack(anchor="w", padx=14, pady=(2, 6))

        self.backup_temp_var = ctk.BooleanVar(value=self.settings.get("backup_to_temp_cache", False))
        self.backup_temp_checkbox = ctk.CTkCheckBox(
            backup_box, text="Lưu ảnh gốc vào bộ nhớ tạm hệ thống",
            variable=self.backup_temp_var, command=self._on_backup_temp_toggle,
            font=ctk.CTkFont(size=12),
        )
        self.backup_temp_checkbox.pack(anchor="w", padx=14, pady=(0, 2))

        backup_temp_hint = ctk.CTkLabel(
            backup_box,
            text="(thay vì lưu cạnh ảnh gốc với hậu tố \"_old\" như mặc định)",
            font=ctk.CTkFont(size=11), text_color="gray", anchor="w",
        )
        backup_temp_hint.pack(anchor="w", padx=32, pady=(0, 4))

        self.temp_path_label = ctk.CTkLabel(
            backup_box,
            text=f"📁  {self.settings.get('temp_cache_dir', '')}   (bấm để mở thư mục)",
            font=ctk.CTkFont(size=11, underline=True), text_color="#4ADE80",
            anchor="w", cursor="hand2",
        )
        self.temp_path_label.pack(anchor="w", padx=32, pady=(0, 12))
        self.temp_path_label.bind("<Button-1>", lambda _e: self._open_temp_cache_folder())

        self._refresh_backup_controls_state()

        # ---------------- Nút bắt đầu + thanh tiến trình ---------------- #
        self.start_btn = ctk.CTkButton(
            self, text="🗜  Bắt đầu nén", command=self._start_compress, width=170, height=38,
            fg_color="#2FA572", hover_color="#248A5D",
        )
        self.start_btn.pack(anchor="w", padx=20, pady=(6, 10))

        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 5))

    # ------------------------------------------------------------------ #
    # Chọn file / thư mục
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

    # ------------------------------------------------------------------ #
    # Tuỳ chọn backup ảnh gốc
    # ------------------------------------------------------------------ #
    def _on_keep_old_toggle(self) -> None:
        self._refresh_backup_controls_state()
        self._persist_backup_settings()

    def _on_backup_temp_toggle(self) -> None:
        self._persist_backup_settings()

    def _refresh_backup_controls_state(self) -> None:
        """Vô hiệu hoá checkbox 'lưu vào bộ nhớ tạm' nếu không giữ ảnh gốc."""
        if self.keep_old_var.get():
            self.backup_temp_checkbox.configure(state="normal")
            self.temp_path_label.configure(text_color="#4ADE80")
        else:
            self.backup_temp_checkbox.configure(state="disabled")
            self.temp_path_label.configure(text_color="gray")

    def _persist_backup_settings(self) -> None:
        """Lưu ngay 2 lựa chọn backup vào settings.json để nhớ cho lần sau."""
        self.settings["keep_old_backup"] = self.keep_old_var.get()
        self.settings["backup_to_temp_cache"] = self.backup_temp_var.get()
        save_settings(self.settings)

    def _open_temp_cache_folder(self) -> None:
        open_folder_in_explorer(self.settings.get("temp_cache_dir", ""))

    # ------------------------------------------------------------------ #
    # Chạy nén
    # ------------------------------------------------------------------ #
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
            compress_directory(
                self.selected_directory, quality, self.emit_event,
                keep_old_backup=settings.get("keep_old_backup", True),
                backup_to_temp=settings.get("backup_to_temp_cache", False),
                temp_cache_dir=settings.get("temp_cache_dir", ""),
            )
        else:
            save_dir = settings.get("save_path")
            compress_file_list(self.selected_files, save_dir, quality, self.emit_event)

        self.emit_event("batch_ui_state", False)
