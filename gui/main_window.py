"""
gui/main_window.py
---------------------
Cửa sổ chính của ứng dụng Software Picture Lite.

Bố cục:
    - Bên trái : Tabview với 3 tab (Nén ảnh đơn / Nén hàng loạt / Cài đặt)
    - Bên phải : Bảng log/tiến trình dùng chung cho toàn bộ ứng dụng

Kiến trúc luồng dữ liệu:
    Các frame con (single/batch) chạy công việc nén ảnh trong background
    thread để không làm treo giao diện. Chúng KHÔNG được phép đụng trực
    tiếp vào widget Tkinter từ thread khác — thay vào đó, chúng gọi
    `self.emit_event(event_type, *args)` để đẩy sự kiện vào hàng đợi
    (queue.Queue). Main thread định kỳ lấy sự kiện ra khỏi hàng đợi
    (`_poll_queue`, chạy qua `after()`) và cập nhật giao diện an toàn.
"""

import os
import queue
import customtkinter as ctk
from PIL import Image

from gui.log_widget import LogPanel
from gui.single_compress_frame import SingleCompressFrame
from gui.batch_compress_frame import BatchCompressFrame
from gui.settings_frame import SettingsFrame

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Software Picture Lite")
        # Kích thước cửa sổ mặc định khi mở app. Muốn to/nhỏ hơn, chỉ cần
        # đổi 2 số này (rộng x cao, đơn vị pixel).
        self.geometry("820x560")
        # Kích thước nhỏ nhất người dùng có thể kéo cửa sổ xuống.
        self.minsize(720, 480)
        self._set_window_icon()

        # Hàng đợi sự kiện — kênh giao tiếp AN TOÀN duy nhất giữa các luồng
        # nén ảnh (background thread) và giao diện (main thread).
        self.event_queue: "queue.Queue" = queue.Queue()

        self._build_layout()
        self._poll_queue()

    # ------------------------------------------------------------------ #
    def _set_window_icon(self) -> None:
        """Gán icon cửa sổ nếu file assets/icon.png tồn tại (không bắt buộc)."""
        icon_path = os.path.join(ASSETS_DIR, "icon.png")
        if os.path.exists(icon_path):
            try:
                icon_image = ctk.CTkImage(Image.open(icon_path), size=(64, 64))
                # iconphoto cần 1 PhotoImage "thật" của tkinter, không phải CTkImage
                import tkinter as tk
                photo = tk.PhotoImage(file=icon_path)
                self.iconphoto(True, photo)
                self._icon_ref = photo  # giữ tham chiếu tránh bị garbage-collected
            except Exception:
                pass  # Icon chỉ là phần trang trí, lỗi ở đây không nên chặn ứng dụng chạy

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ---- Khung Tabview chứa các chức năng chính (bên trái) ---- #
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=(15, 8), pady=15)

        tab_single = self.tabview.add("Nén ảnh đơn")
        tab_batch = self.tabview.add("Nén hàng loạt")
        tab_settings = self.tabview.add("Cài đặt")

        # ---- Khung log/tiến trình (bên phải) ---- #
        log_container = ctk.CTkFrame(self, corner_radius=12)
        log_container.grid(row=0, column=1, sticky="nsew", padx=(8, 15), pady=15)
        log_container.grid_rowconfigure(1, weight=1)
        log_container.grid_columnconfigure(0, weight=1)

        log_title = ctk.CTkLabel(
            log_container, text="📋  Nhật ký tiến trình", font=ctk.CTkFont(size=16, weight="bold")
        )
        log_title.grid(row=0, column=0, sticky="w", padx=15, pady=(15, 8))

        self.log_panel = LogPanel(log_container, fg_color="transparent")
        self.log_panel.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 15))

        # ---- Khởi tạo các tab chức năng, truyền vào emit_event để gửi log an toàn ---- #
        self.single_frame = SingleCompressFrame(tab_single, self.emit_event)
        self.single_frame.pack(fill="both", expand=True)

        self.batch_frame = BatchCompressFrame(tab_batch, self.emit_event)
        self.batch_frame.pack(fill="both", expand=True)

        self.settings_frame = SettingsFrame(tab_settings)
        self.settings_frame.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    # Cơ chế hàng đợi sự kiện (thread-safe communication)
    # ------------------------------------------------------------------ #
    def emit_event(self, event_type: str, *args) -> None:
        """
        Được gọi từ các luồng nén ảnh (background thread) để gửi 1 sự kiện
        cập nhật giao diện. Hàm này CHỈ đẩy dữ liệu vào hàng đợi — an toàn
        để gọi từ bất kỳ thread nào.
        """
        self.event_queue.put((event_type, args))

    def _poll_queue(self) -> None:
        """Định kỳ lấy sự kiện ra khỏi hàng đợi và cập nhật UI (chạy trên main thread)."""
        try:
            while True:
                event_type, args = self.event_queue.get_nowait()
                self._handle_event(event_type, args)
        except queue.Empty:
            pass
        finally:
            self.after(80, self._poll_queue)

    def _handle_event(self, event_type: str, args: tuple) -> None:
        if event_type == "progress":
            self.log_panel.log_progress(*args)
        elif event_type == "success":
            self.log_panel.log_success(*args)
        elif event_type == "skip":
            self.log_panel.log_skip(*args)
        elif event_type == "info":
            self.log_panel.log_info(*args)
        elif event_type == "completed":
            self.log_panel.log_completed()
        elif event_type == "batch_ui_state":
            self.batch_frame.set_running_state(*args)
        elif event_type == "single_ui_state":
            self.single_frame.set_running_state(*args)
