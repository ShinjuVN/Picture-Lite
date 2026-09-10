"""
main.py
---------
Điểm khởi chạy chính của ứng dụng Software Picture Lite.

Chạy ứng dụng bằng lệnh:
    python main.py
"""

from gui.main_window import MainWindow


def main() -> None:
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
