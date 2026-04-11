import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from PIL import Image, ImageTk, ImageOps, ImageEnhance

from config import (
    ACCENT,
    ACCENT_HOVER,
    APP_BG,
    AUTHOR_NAME,
    BORDER,
    CARD_BG,
    CARD_BG_2,
    CARD_BG_3,
    SUCCESS,
    TEXTBOX_BG,
    TEXT_MAIN,
    TEXT_SUB,
    WARNING,
)
from services.link_service import MEET_LINK_PATTERN
from services.ocr_service import (
    extract_meet_links_from_ocr_text,
    get_image_from_clipboard,
    has_pytesseract,
    image_to_text,
    #normalize_ocr_text,
)
from ui.dialogs import show_pretty_notice


class ScanImageWindow:
    PREVIEW_SIZE = (420, 240)
    PREVIEW_BOX_HEIGHT = 260
    RESULT_BOX_MIN_HEIGHT = 220

    def __init__(self, parent_app):
        self.app = parent_app
        self.window = None
        self.scan_image_pil = None
        self.scan_preview_photo = None

        self.scan_preview_box = None
        self.scan_preview_canvas = None
        self.scan_preview_hbar = None
        self.scan_preview_vbar = None
        self.scan_preview_label = None
        self.scan_result_text = None
        self.scan_path_var = None
        self.scan_stats_var = None
        self.preview_display_image = None
        self.preview_scale = 1.0
        self.scan_stats_var = None

    def clear_scan_image(self):
        self.scan_image_pil = None
        self.preview_display_image = None
        self.preview_scale = 1.0

        if self.scan_preview_label is not None:
            self.scan_preview_label.configure(image="", text="Chưa có ảnh")

        if self.scan_preview_canvas is not None:
            self.scan_preview_canvas.configure(scrollregion=(0, 0, 1, 1))

        if self.scan_path_var is not None:
            self.scan_path_var.set("Chưa có ảnh nào được chọn.")

        self.set_scan_result_text("")

        if self.scan_stats_var is not None:
            self.scan_stats_var.set("Tổng link phát hiện: 0\nLink hợp lệ: 0\nLink không hợp lệ: 0")

    def _refresh_preview_fit(self, _event=None):
        if self.scan_image_pil is None or self.scan_preview_canvas is None:
            return

        canvas_w = max(1, self.scan_preview_canvas.winfo_width() - 4)
        canvas_h = max(1, self.scan_preview_canvas.winfo_height() - 4)

        img = self.scan_image_pil.copy()
        img_w, img_h = img.size

        if img_w <= 0 or img_h <= 0:
            return

        scale = min(canvas_w / img_w, canvas_h / img_h)
        if scale <= 0:
            scale = 1.0

        new_w = max(1, int(img_w * scale))
        new_h = max(1, int(img_h * scale))

        display = img.resize((new_w, new_h), Image.LANCZOS)
        self.preview_display_image = ImageTk.PhotoImage(display)
        self.preview_scale = scale

        self.scan_preview_label.configure(image=self.preview_display_image, text="")
        self.scan_preview_canvas.itemconfigure(self.scan_preview_canvas_window, width=new_w, height=new_h)

        x = max(0, (canvas_w - new_w) // 2)
        y = max(0, (canvas_h - new_h) // 2)
        self.scan_preview_canvas.coords(self.scan_preview_canvas_window, x, y)
        self.scan_preview_canvas.configure(scrollregion=(0, 0, max(canvas_w, new_w), max(canvas_h, new_h)))

    def _build_ocr_source_image(self) -> Image.Image | None:
        if self.scan_image_pil is None:
            return None

        image = self.scan_image_pil.convert("RGB")
        width, height = image.size

        if width < 1400:
            scale = 2
            image = image.resize((width * scale, height * scale), Image.LANCZOS)

        image = ImageEnhance.Sharpness(image).enhance(1.8)
        image = ImageEnhance.Contrast(image).enhance(1.15)
        return image

    def open(self):
        if self.window is not None and self.window.winfo_exists():
            self.window.focus_force()
            return

        win = tk.Toplevel(self.app)
        self.window = win
        win.title("Quét ảnh")
        win.geometry("980x700")
        win.minsize(900, 640)
        win.configure(bg=APP_BG)
        win.transient(self.app)
        win.grab_set()
        win.focus_force()

        try:
            if self.app.app_icon_photo is not None:
                win.iconphoto(True, self.app.app_icon_photo)
        except Exception:
            pass

        wrapper = tk.Frame(
            win,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            bd=0,
        )
        wrapper.pack(fill="both", expand=True, padx=18, pady=18)
        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=5)
        wrapper.grid_columnconfigure(1, weight=2)

        left = tk.Frame(wrapper, bg=CARD_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(18, 12), pady=18)
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(4, weight=3)
        left.grid_rowconfigure(6, weight=2)

        right = tk.Frame(wrapper, bg=CARD_BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 18), pady=18)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(5, weight=1)

        tk.Label(
            left,
            text="Quét ảnh lấy link Google Meet",
            bg=CARD_BG,
            fg=TEXT_MAIN,
            font=("Segoe UI Semibold", 17),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            left,
            text="Chọn ảnh hoặc paste ảnh. Kết quả cuối cùng sẽ hiện ở ô bên dưới.",
            bg=CARD_BG,
            fg=TEXT_SUB,
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(8, 16))

        action_bar = tk.Frame(left, bg=CARD_BG)
        action_bar.grid(row=2, column=0, sticky="w", pady=(0, 14))

        choose_btn = tk.Button(
            action_bar,
            text="📁  Chọn ảnh",
            command=self.choose_image,
            bg=CARD_BG_3,
            fg=TEXT_MAIN,
            activebackground="#1b2a49",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=10,
            cursor="hand2",
        )
        choose_btn.grid(row=0, column=0, sticky="w")

        paste_btn = tk.Button(
            action_bar,
            text="📋  Paste ảnh",
            command=self.paste_image_from_clipboard,
            bg=CARD_BG_3,
            fg=TEXT_MAIN,
            activebackground="#1b2a49",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=10,
            cursor="hand2",
        )
        paste_btn.grid(row=0, column=1, sticky="w", padx=(8, 0))

        clear_image_btn = tk.Button(
            action_bar,
            text="🗑  Xóa ảnh",
            command=self.clear_scan_image,
            bg=CARD_BG_2,
            fg=TEXT_MAIN,
            activebackground="#334155",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=10,
            cursor="hand2",
        )
        clear_image_btn.grid(row=0, column=2, sticky="w", padx=(8, 0))

        tk.Label(
            left,
            text="Ảnh xem trước",
            bg=CARD_BG,
            fg=TEXT_MAIN,
            font=("Segoe UI Semibold", 11),
            anchor="w",
        ).grid(row=3, column=0, sticky="w", pady=(0, 8))

        self.scan_preview_box = tk.Frame(
            left,
            bg=TEXTBOX_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            bd=0,
            height=300,
        )
        self.scan_preview_box.grid(row=4, column=0, sticky="nsew")
        self.scan_preview_box.grid_propagate(False)
        self.scan_preview_box.grid_rowconfigure(0, weight=1)
        self.scan_preview_box.grid_columnconfigure(0, weight=1)

        self.scan_preview_canvas = tk.Canvas(
            self.scan_preview_box,
            bg=TEXTBOX_BG,
            highlightthickness=0,
            bd=0,
            xscrollincrement=1,
            yscrollincrement=1,
        )
        self.scan_preview_canvas.grid(row=0, column=0, sticky="nsew")

        self.scan_preview_vbar = ttk.Scrollbar(
            self.scan_preview_box,
            orient="vertical",
            command=self.scan_preview_canvas.yview,
        )
        self.scan_preview_vbar.grid(row=0, column=1, sticky="ns")

        self.scan_preview_hbar = ttk.Scrollbar(
            self.scan_preview_box,
            orient="horizontal",
            command=self.scan_preview_canvas.xview,
        )
        self.scan_preview_hbar.grid(row=1, column=0, sticky="ew")

        self.scan_preview_canvas.configure(
            xscrollcommand=self.scan_preview_hbar.set,
            yscrollcommand=self.scan_preview_vbar.set,
        )

        self.scan_preview_label = tk.Label(
            self.scan_preview_canvas,
            text="Chưa có ảnh",
            bg=TEXTBOX_BG,
            fg=TEXT_SUB,
            font=("Segoe UI", 11),
            justify="center",
        )

        self.scan_preview_canvas_window = self.scan_preview_canvas.create_window(
            (0, 0),
            window=self.scan_preview_label,
            anchor="nw",
        )

        self.scan_preview_canvas.bind("<Configure>", self._refresh_preview_fit)
        self.scan_preview_canvas.bind("<Button-1>", lambda _e: self.paste_image_from_clipboard())

        tk.Label(
            left,
            text="Kết quả cuối cùng",
            bg=CARD_BG,
            fg=TEXT_MAIN,
            font=("Segoe UI Semibold", 11),
            anchor="w",
        ).grid(row=5, column=0, sticky="w", pady=(18, 8))

        result_wrap = tk.Frame(left, bg=CARD_BG)
        result_wrap.grid(row=6, column=0, sticky="nsew")
        result_wrap.grid_rowconfigure(0, weight=1)
        result_wrap.grid_columnconfigure(0, weight=1)
        result_wrap.configure(height=220)
        result_wrap.grid_propagate(False)

        self.scan_result_text = tk.Text(
            result_wrap,
            wrap="word",
            font=("Consolas", 11),
            bg=TEXTBOX_BG,
            fg=TEXT_MAIN,
            insertbackground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=14,
            highlightthickness=0,
            undo=False,
        )
        self.scan_result_text.grid(row=0, column=0, sticky="nsew")

        result_scroll = ttk.Scrollbar(result_wrap, orient="vertical", command=self.scan_result_text.yview)
        result_scroll.grid(row=0, column=1, sticky="ns")
        self.scan_result_text.configure(yscrollcommand=result_scroll.set)

        self.scan_result_text.bind("<Key>", lambda e: "break")
        self.scan_result_text.bind("<Control-v>", lambda e: "break")
        self.scan_result_text.bind("<Control-x>", lambda e: "break")
        self.scan_result_text.bind("<BackSpace>", lambda e: "break")
        self.scan_result_text.bind("<Delete>", lambda e: "break")

        tk.Label(
            right,
            text="Ảnh đã chọn",
            bg=CARD_BG,
            fg=TEXT_MAIN,
            font=("Segoe UI Semibold", 11),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.scan_path_var = tk.StringVar(value="Chưa có ảnh nào được chọn.")
        tk.Label(
            right,
            textvariable=self.scan_path_var,
            bg=CARD_BG,
            fg=TEXT_SUB,
            font=("Segoe UI", 9),
            justify="left",
            anchor="w",
            wraplength=260,
        ).grid(row=1, column=0, sticky="ew", pady=(8, 14))

        stats_card = tk.Frame(
            right,
            bg=CARD_BG_2,
            highlightbackground=BORDER,
            highlightthickness=1,
            bd=0,
        )
        stats_card.grid(row=2, column=0, sticky="ew", pady=(0, 16))

        tk.Label(
            stats_card,
            text="Thống kê",
            bg=CARD_BG_2,
            fg=TEXT_MAIN,
            font=("Segoe UI Semibold", 11),
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self.scan_stats_var = tk.StringVar(
            value="Tổng link phát hiện: 0\nLink hợp lệ: 0\nLink không hợp lệ: 0"
        )
        tk.Label(
            stats_card,
            textvariable=self.scan_stats_var,
            bg=CARD_BG_2,
            fg=TEXT_SUB,
            font=("Segoe UI", 10),
            justify="left",
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(0, 14))

        scan_btn = tk.Button(
            right,
            text="✨  Quét và thêm link",
            command=self.scan_selected_image,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=12,
            cursor="hand2",
        )
        scan_btn.grid(row=3, column=0, sticky="ew", pady=(4, 8))

        transfer_btn = tk.Button(
            right,
            text="📥  Chuyển kết quả",
            command=self.transfer_result_to_main,
            bg=CARD_BG_3,
            fg=TEXT_MAIN,
            activebackground="#1b2a49",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=12,
            cursor="hand2",
        )
        transfer_btn.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        close_btn = tk.Button(
            right,
            text="Đóng",
            command=self.close,
            bg=CARD_BG_2,
            fg=TEXT_MAIN,
            activebackground="#334155",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=12,
            cursor="hand2",
        )
        close_btn.grid(row=5, column=0, sticky="ew")

        self.set_scan_result_text("")

        win.protocol("WM_DELETE_WINDOW", self.close)
        win.bind("<Control-v>", lambda _e: self.paste_image_from_clipboard())
        self.scan_preview_box.bind("<Control-v>", lambda _e: self.paste_image_from_clipboard())
        self.scan_preview_label.bind("<Control-v>", lambda _e: self.paste_image_from_clipboard())

    def _setup_result_tags(self):
        self.scan_result_text.tag_configure("section", foreground=TEXT_SUB, font=("Segoe UI Semibold", 10))
        self.scan_result_text.tag_configure("valid_link", foreground=SUCCESS)
        self.scan_result_text.tag_configure("invalid_link", foreground=WARNING)

    def _prevent_result_edit(self, event):
        if (event.state & 0x4) and event.keysym.lower() == "c":
            return None
        if event.keysym in {"Left", "Right", "Up", "Down", "Home", "End", "Prior", "Next"}:
            return None
        return "break"

    def close(self):
        if self.window is not None and self.window.winfo_exists():
            try:
                self.window.grab_release()
            except Exception:
                pass
            self.window.destroy()

        self.window = None
        self.scan_image_pil = None
        self.scan_preview_photo = None

    def choose_image(self):
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="Chọn ảnh để quét",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.webp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("Bitmap", "*.bmp"),
                ("WebP", "*.webp"),
            ],
        )

        if not file_path:
            return

        try:
            image = Image.open(file_path).convert("RGBA")
            self.set_scan_image(image=image, source_text=str(Path(file_path)))
        except Exception as exc:
            show_pretty_notice(
                self.app,
                "error",
                "Không mở được ảnh",
                "❌",
                f"{AUTHOR_NAME} không thể mở ảnh này.\n\nChi tiết: {exc}",
                self.app.app_icon_photo,
            )

    def paste_image_from_clipboard(self):
        image = get_image_from_clipboard(self.app)
        if image is not None:
            self.set_scan_image(image=image, source_text="Ảnh được paste từ clipboard")
            return

        show_pretty_notice(
            self.app,
            "warning",
            "Clipboard chưa có ảnh",
            "📋",
            (
                f"{AUTHOR_NAME} chưa tìm thấy ảnh trong clipboard.\n\n"
                f"Bạn có thể:\n"
                f"• copy trực tiếp một ảnh\n"
                f"• hoặc copy đường dẫn file ảnh"
            ),
            self.app.app_icon_photo,
        )

    def set_scan_image(self, image, source_text: str):
        self.scan_image_pil = image
        self.scan_path_var.set(source_text)
        self._refresh_preview_fit()

    def _set_scan_stats(self, total: int, valid: int, invalid: int):
        self.scan_stats_var.set(
            f"Tổng link phát hiện: {total}\n"
            f"Link hợp lệ: {valid}\n"
            f"Link không hợp lệ: {invalid}"
        )

    def set_scan_result_text(self, text: str):
        self.scan_result_text.configure(state="normal")
        self.scan_result_text.delete("1.0", "end")
        if text.strip():
            self.scan_result_text.insert("1.0", text)
        else:
            self.scan_result_text.insert("1.0", "[Chưa có kết quả]")
        self.scan_result_text.configure(state="normal")

    def transfer_result_to_main(self):
        if self.scan_result_text is None:
            return

        raw_text = self.scan_result_text.get("1.0", "end-1c").strip()

        if not raw_text or raw_text == "[Chưa có kết quả]" or raw_text == "[Không tìm thấy link Google Meet hợp lệ]":
            show_pretty_notice(
                self.app,
                "warning",
                "Chưa có kết quả để chuyển",
                "📭",
                f"{AUTHOR_NAME} chưa thấy link nào trong ô kết quả để chuyển sang form chính.",
                self.app.app_icon_photo,
            )
            return

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not lines:
            show_pretty_notice(
                self.app,
                "warning",
                "Chưa có kết quả để chuyển",
                "📭",
                f"{AUTHOR_NAME} chưa thấy link nào trong ô kết quả để chuyển sang form chính.",
                self.app.app_icon_photo,
            )
            return

        current = self.app.textbox.get("1.0", "end-1c").strip()
        insert_text = "\n".join(lines)

        if current:
            self.app.textbox.insert("end", "\n" + insert_text)
        else:
            self.app.textbox.insert("1.0", insert_text)

        self.app.update_link_count()

        show_pretty_notice(
            self.app,
            "success",
            "Đã chuyển kết quả",
            "📥",
            (
                f"{AUTHOR_NAME} đã chuyển {len(lines)} dòng kết quả sang ô Danh sách link "
                f"ở form chính."
            ),
            self.app.app_icon_photo,
        )

    def scan_selected_image(self):
        if self.scan_image_pil is None:
            show_pretty_notice(
                self.app,
                "warning",
                "Chưa có ảnh để quét",
                "🖼️",
                f"{AUTHOR_NAME} nhắc bạn hãy chọn ảnh hoặc paste ảnh trước khi quét nhé.",
                self.app.app_icon_photo,
            )
            return

        if not has_pytesseract():
            show_pretty_notice(
                self.app,
                "error",
                "Thiếu thư viện OCR",
                "⚙️",
                (
                    f"{AUTHOR_NAME} chưa thể quét ảnh vì máy hiện tại chưa có pytesseract.\n\n"
                    f"Cài bằng lệnh: pip install pytesseract"
                ),
                self.app.app_icon_photo,
            )
            return

        try:
            ocr_source = self._build_ocr_source_image()
            ocr_text = image_to_text(ocr_source, lang="eng+vie")
        except Exception as exc:
            show_pretty_notice(
                self.app,
                "error",
                "Quét ảnh thất bại",
                "❌",
                f"{AUTHOR_NAME} không thể quét ảnh này.\n\nChi tiết: {exc}",
                self.app.app_icon_photo,
            )
            return

        found_links = extract_meet_links_from_ocr_text(ocr_text)
        valid_links = [link for link in found_links if MEET_LINK_PATTERN.match(link)]
        invalid_links = [link for link in found_links if not MEET_LINK_PATTERN.match(link)]

        final_result = "\n".join(found_links) if found_links else "[Không tìm thấy link Google Meet hợp lệ]"
        self.set_scan_result_text(final_result)

        # if found_links:
        #     current = self.app.textbox.get("1.0", "end-1c").strip()
        #     insert_text = "\n".join(found_links)

        #     if current:
        #         self.app.textbox.insert("end", "\n" + insert_text)
        #     else:
        #         self.app.textbox.insert("1.0", insert_text)

        #     self.app.update_link_count()

        self.scan_stats_var.set(
            f"Tổng link phát hiện: {len(found_links)}\n"
            f"Link hợp lệ: {len(valid_links)}\n"
            f"Link không hợp lệ: {len(invalid_links)}"
        )

        show_pretty_notice(
            self.app,
            "success",
            "Quét ảnh hoàn tất",
            "✨",
            (
                f"{AUTHOR_NAME} đã quét xong ảnh.\n\n"
                f"Tìm thấy {len(found_links)} link.\n"
                f"Link hợp lệ: {len(valid_links)}\n"
                f"Link không hợp lệ: {len(invalid_links)}"
            ),
            self.app.app_icon_photo,
        )