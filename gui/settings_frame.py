"""
gui/settings_frame.py
-----------------------
Giao diện tab "Cài đặt": cho phép người dùng tuỳ chỉnh đường dẫn lưu
mặc định và mức chất lượng nén, sau đó lưu xuống config/settings.json.
"""

import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.settings_manager import load_settings, save_settings


class SettingsFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = load_settings()
        self._build_ui()

    def _build_ui(self) -> None:
        title = ctk.CTkLabel(self, text="⚙️  Cài đặt ứng dụng", font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(anchor="w", padx=20, pady=(20, 15))

        # ---------------- Đường dẫn lưu mặc định ---------------- #
        path_label = ctk.CTkLabel(self, text="Đường dẫn lưu mặc định", font=ctk.CTkFont(size=14, weight="bold"))
        path_label.pack(anchor="w", padx=20, pady=(10, 4))

        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.pack(fill="x", padx=20)

        self.path_entry = ctk.CTkEntry(path_row, placeholder_text="Chọn thư mục lưu ảnh đã nén...")
        self.path_entry.insert(0, self.settings.get("save_path", ""))
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8), ipady=4)

        browse_btn = ctk.CTkButton(path_row, text="Duyệt...", width=90, command=self._browse_folder)
        browse_btn.pack(side="left")

        hint_path = ctk.CTkLabel(
            self,
            text="Áp dụng cho: nén ảnh đơn & nén nhiều ảnh rời. "
                 "(Khi quét cả thư mục, ảnh sẽ được thay thế ngay tại vị trí gốc.)",
            font=ctk.CTkFont(size=11), text_color="gray", wraplength=560, justify="left",
        )
        hint_path.pack(anchor="w", padx=20, pady=(4, 0))

        # ---------------- Mức chất lượng nén ---------------- #
        quality_label = ctk.CTkLabel(self, text="Mức chất lượng nén", font=ctk.CTkFont(size=14, weight="bold"))
        quality_label.pack(anchor="w", padx=20, pady=(24, 4))

        quality_row = ctk.CTkFrame(self, fg_color="transparent")
        quality_row.pack(fill="x", padx=20)

        self.quality_value_label = ctk.CTkLabel(
            quality_row, text=str(self.settings.get("quality", 85)), width=45,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.quality_value_label.pack(side="right")

        self.quality_slider = ctk.CTkSlider(
            quality_row, from_=1, to=100, number_of_steps=99, command=self._on_quality_change
        )
        self.quality_slider.set(self.settings.get("quality", 85))
        self.quality_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        hint_quality = ctk.CTkLabel(
            self,
            text="Chất lượng thấp → dung lượng nhỏ hơn nhiều. Chất lượng cao → giữ chi tiết ảnh tốt hơn. "
                 "Khuyến nghị: 75 - 90.",
            font=ctk.CTkFont(size=11), text_color="gray", wraplength=560, justify="left",
        )
        hint_quality.pack(anchor="w", padx=20, pady=(4, 0))

        # ---------------- Nút lưu ---------------- #
        save_btn = ctk.CTkButton(
            self, text="💾  Lưu cài đặt", command=self._save, height=38, width=160,
            fg_color="#2FA572", hover_color="#248A5D",
        )
        save_btn.pack(anchor="w", padx=20, pady=(32, 6))

        self.status_label = ctk.CTkLabel(self, text="", text_color="#4ADE80", font=ctk.CTkFont(size=12))
        self.status_label.pack(anchor="w", padx=20)

    # ------------------------------------------------------------------ #
    def _browse_folder(self) -> None:
        folder = filedialog.askdirectory(title="Chọn thư mục lưu mặc định")
        if folder:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, folder)

    def _on_quality_change(self, value) -> None:
        self.quality_value_label.configure(text=str(int(value)))

    def _save(self) -> None:
        save_path = self.path_entry.get().strip()
        if not save_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn đường dẫn lưu hợp lệ.")
            return

        try:
            os.makedirs(save_path, exist_ok=True)
        except OSError as error:
            messagebox.showerror("Lỗi", f"Không thể tạo/truy cập thư mục:\n{error}")
            return

        self.settings["save_path"] = save_path
        self.settings["quality"] = int(self.quality_slider.get())
        save_settings(self.settings)

        self.status_label.configure(text="✓ Đã lưu cài đặt thành công.")
        self.after(2500, lambda: self.status_label.configure(text=""))
