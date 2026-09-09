"""
gui/log_widget.py
-------------------
Widget hiển thị log / tiến trình nén ảnh theo phong cách console.

Định dạng các dòng log:
    </> anh1.png [xx%]                              -> đang nén
    </> Đã lưu anh1.png về đường dẫn: <path>         -> hoàn thành 1 file
    </> anh1.png bỏ qua | Lý do: Đã nén              -> bị bỏ qua
    </> Completed                                    -> kết thúc toàn bộ

Dòng tiến trình [xx%] được CẬP NHẬT TẠI CHỖ (ghi đè) mỗi khi phần trăm
thay đổi, thay vì tạo dòng mới liên tục, giữ cho log gọn gàng dễ theo dõi.
"""

import customtkinter as ctk


class LogPanel(ctk.CTkFrame):
    """Bảng hiển thị log/tiến trình dạng console, chỉ đọc (read-only)."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.textbox = ctk.CTkTextbox(
            self,
            wrap="none",
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color="#101012",
            text_color="#4ADE80",
        )
        self.textbox.pack(fill="both", expand=True)
        self.textbox.configure(state="disabled")

        # True nếu dòng cuối cùng hiện đang là dòng tiến trình (có thể bị ghi đè)
        self._progress_line_active = False

    # ------------------------------------------------------------------ #
    # Hàm nội bộ: thêm / ghi đè 1 dòng log
    # ------------------------------------------------------------------ #
    def _append_line(self, text: str, is_progress: bool) -> None:
        self.textbox.configure(state="normal")

        if self._progress_line_active:
            # Xoá dòng tiến trình trước đó (từ đầu dòng áp chót đến đầu dòng cuối,
            # tức là xoá trọn dòng progress bao gồm cả ký tự xuống dòng của nó)
            self.textbox.delete("end-2l", "end-1l")

        self.textbox.insert("end", text + "\n")
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

        self._progress_line_active = is_progress

    # ------------------------------------------------------------------ #
    # API công khai — dùng bởi main_window khi xử lý sự kiện từ hàng đợi
    # ------------------------------------------------------------------ #
    def log_progress(self, filename: str, percent: int) -> None:
        """Hiển thị / cập nhật dòng tiến trình đang nén."""
        self._append_line(f"</> {filename} [{int(percent)}%]", is_progress=True)

    def log_success(self, filename: str, save_path: str) -> None:
        """Hiển thị dòng thông báo đã nén & lưu thành công."""
        self._append_line(f"</> Đã lưu {filename} về đường dẫn: {save_path}", is_progress=False)

    def log_skip(self, filename: str, reason: str) -> None:
        """Hiển thị dòng thông báo bỏ qua kèm lý do."""
        self._append_line(f"</> {filename} bỏ qua | Lý do: {reason}", is_progress=False)

    def log_info(self, message: str) -> None:
        """Hiển thị 1 dòng thông tin chung (không thuộc file cụ thể nào)."""
        self._append_line(f"</> {message}", is_progress=False)

    def log_completed(self) -> None:
        """Hiển thị dòng đánh dấu kết thúc toàn bộ tiến trình."""
        self._append_line("</> Completed", is_progress=False)

    def clear(self) -> None:
        """Xoá toàn bộ nội dung log hiện tại."""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")
        self._progress_line_active = False
