import time
import subprocess
import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk, ImageOps

from config import (
    ACCENT,
    ACCENT_HOVER,
    APP_BG,
    APP_ICON_PATH,
    AUTHOR_NAME,
    BORDER,
    BROWSER_LOGOS,
    CARD_BG,
    CARD_BG_2,
    CARD_BG_3,
    ICON_BOX_SIZE,
    ICON_IMAGE_SIZE,
    SELECT_BORDER,
    SUCCESS,
    TEXTBOX_BG,
    TEXT_MAIN,
    TEXT_SUB,
    WARNING,
)
from services.browser_service import load_installed_browsers
from services.link_service import analyze_links
from ui.dialogs import show_pretty_notice
from ui.scan_window import ScanImageWindow


class BrowserMeetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GG Meet Link Opener")
        self.geometry("1200x700")
        self.minsize(980, 680)
        self.configure(bg=APP_BG)

        self.selected_browser = None
        self.browser_buttons = {}
        self.logo_images = {}
        self._window_resize_job = None
        self.app_icon_photo = None
        self.scan_window_manager = ScanImageWindow(self)

        self.detected_data = load_installed_browsers()
        self.detected_browsers = self.detected_data["browsers"]

        self._set_app_icon()
        self._setup_style()
        self._build_ui()
        self._populate_browsers()
        self._auto_select_default()
        self._load_local_logos()
        self.update_link_count()

        self.bind("<Configure>", self._on_window_resize)

    def _set_app_icon(self):
        try:
            if APP_ICON_PATH.is_file():
                icon_image = Image.open(APP_ICON_PATH).convert("RGBA")
                icon_image = ImageOps.contain(icon_image, (64, 64), Image.LANCZOS)
                self.app_icon_photo = ImageTk.PhotoImage(icon_image)
                self.iconphoto(True, self.app_icon_photo)
        except Exception:
            pass

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=APP_BG)

    def _build_ui(self):
        self.root_frame = tk.Frame(self, bg=APP_BG)
        self.root_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.root_frame.grid_rowconfigure(1, weight=1)
        self.root_frame.grid_rowconfigure(2, weight=0)
        self.root_frame.grid_columnconfigure(0, weight=1)

        header = tk.Frame(self.root_frame, bg=APP_BG)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(0, weight=1)

        tk.Label(
            header,
            text="GG Meet Link Opener",
            bg=APP_BG,
            fg=TEXT_MAIN,
            font=("Segoe UI Semibold", 24),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        tk.Label(
            header,
            text="Dán nhiều link Google Meet, chọn trình duyệt đang có trong máy, rồi mở toàn bộ.",
            bg=APP_BG,
            fg=TEXT_SUB,
            font=("Segoe UI", 11),
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        content = tk.Frame(self.root_frame, bg=APP_BG)
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=4)
        content.grid_columnconfigure(1, weight=1)

        self.left_card = tk.Frame(
            content,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            bd=0,
        )
        self.left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.right_card = tk.Frame(
            content,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
            bd=0,
        )
        self.right_card.grid(row=0, column=1, sticky="nsew")

        self._build_left_panel()
        self._build_right_panel()

        footer = tk.Frame(self.root_frame, bg=APP_BG)
        footer.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        footer.grid_columnconfigure(0, weight=1)

        tk.Label(
            footer,
            text=f"Tác giả: {AUTHOR_NAME}",
            bg=APP_BG,
            fg=TEXT_SUB,
            font=("Segoe UI Semibold", 10),
            anchor="e",
        ).grid(row=0, column=0, sticky="e")

    def _build_left_panel(self):
        self.left_card.grid_rowconfigure(3, weight=1)
        self.left_card.grid_columnconfigure(0, weight=1)

        tk.Label(
            self.left_card,
            text="Danh sách link",
            bg=CARD_BG,
            fg=TEXT_MAIN,
            font=("Segoe UI Semibold", 12),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 0))

        top_tools = tk.Frame(self.left_card, bg=CARD_BG)
        top_tools.grid(row=1, column=0, sticky="ew", padx=18, pady=(10, 10))
        top_tools.grid_columnconfigure(0, weight=1)

        tk.Label(
            top_tools,
            text="Mỗi dòng một link, hoặc paste cả khối text. App sẽ tự tách URL.",
            bg=CARD_BG,
            fg=TEXT_SUB,
            font=("Segoe UI", 10),
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        self.scan_button = tk.Button(
            top_tools,
            text="🖼️  Quét ảnh",
            command=self.open_scan_image_window,
            bg=CARD_BG_3,
            fg=TEXT_MAIN,
            activebackground="#1b2a49",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 10),
            padx=14,
            pady=9,
            cursor="hand2",
        )
        self.scan_button.grid(row=0, column=1, sticky="e")

        text_wrap = tk.Frame(self.left_card, bg=CARD_BG)
        text_wrap.grid(row=3, column=0, sticky="nsew", padx=18)
        text_wrap.grid_rowconfigure(0, weight=1)
        text_wrap.grid_columnconfigure(0, weight=1)

        self.textbox = tk.Text(
            text_wrap,
            wrap="word",
            font=("Consolas", 11),
            bg=TEXTBOX_BG,
            fg=TEXT_MAIN,
            insertbackground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=14,
            undo=True,
            selectbackground=ACCENT,
            highlightthickness=0,
        )
        self.textbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(text_wrap, orient="vertical", command=self.textbox.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.textbox.configure(yscrollcommand=scrollbar.set)

        quick_actions = tk.Frame(self.left_card, bg=CARD_BG)
        quick_actions.grid(row=4, column=0, sticky="ew", padx=18, pady=(12, 0))

        self.paste_btn = self._make_action_button(quick_actions, "Dán từ clipboard", self.paste_from_clipboard)
        self.paste_btn.grid(row=0, column=0, sticky="w")

        self.clear_btn = self._make_action_button(quick_actions, "Xóa", self.clear_text)
        self.clear_btn.grid(row=0, column=1, sticky="w", padx=(8, 0))

        bottom_bar = tk.Frame(self.left_card, bg=CARD_BG)
        bottom_bar.grid(row=5, column=0, sticky="ew", padx=18, pady=(14, 18))
        bottom_bar.grid_columnconfigure(1, weight=1)

        info_wrap = tk.Frame(bottom_bar, bg=CARD_BG)
        info_wrap.grid(row=0, column=0, sticky="w")

        self.link_count_var = tk.StringVar(value="Số link hợp lệ: 0")
        tk.Label(
            info_wrap,
            textvariable=self.link_count_var,
            bg=CARD_BG,
            fg=TEXT_SUB,
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
        ).pack(anchor="w")

        self.link_note_var = tk.StringVar(value="")
        self.link_note_label = tk.Label(
            info_wrap,
            textvariable=self.link_note_var,
            bg=CARD_BG,
            fg=WARNING,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=520,
        )
        self.link_note_label.pack(anchor="w", pady=(4, 0))

        self.open_button = tk.Button(
            bottom_bar,
            text="Mở tất cả link",
            command=self.open_links,
            bg=ACCENT,
            fg="white",
            activebackground=ACCENT_HOVER,
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 10),
            padx=22,
            pady=10,
            cursor="hand2",
            width=18,
        )
        self.open_button.grid(row=0, column=2, sticky="e")

        self.textbox.bind("<<Modified>>", self._on_text_change)

    def _build_right_panel(self):
        self.right_card.grid_rowconfigure(2, weight=1)
        self.right_card.grid_columnconfigure(0, weight=1)

        tk.Label(
            self.right_card,
            text="Chọn trình duyệt",
            bg=CARD_BG,
            fg=TEXT_MAIN,
            font=("Segoe UI Semibold", 12),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 0))

        default_name = self.detected_data.get("default_browser_name") or "Không xác định"
        self.default_browser_label = tk.Label(
            self.right_card,
            text=f"Trình duyệt mặc định: {default_name}",
            bg=CARD_BG,
            fg=TEXT_SUB,
            font=("Segoe UI", 10),
            anchor="w",
            justify="left",
        )
        self.default_browser_label.grid(row=1, column=0, sticky="ew", padx=18, pady=(6, 10))

        browser_wrap = tk.Frame(self.right_card, bg=CARD_BG)
        browser_wrap.grid(row=2, column=0, sticky="nsew", padx=18)
        browser_wrap.grid_rowconfigure(0, weight=1)
        browser_wrap.grid_columnconfigure(0, weight=1)

        self.browser_list_canvas = tk.Canvas(
            browser_wrap,
            bg=CARD_BG,
            highlightthickness=0,
            bd=0,
        )
        self.browser_list_canvas.grid(row=0, column=0, sticky="nsew")

        browser_scrollbar = ttk.Scrollbar(
            browser_wrap,
            orient="vertical",
            command=self.browser_list_canvas.yview,
        )
        browser_scrollbar.grid(row=0, column=1, sticky="ns")

        self.browser_list_canvas.configure(yscrollcommand=browser_scrollbar.set)

        self.browser_list_frame = tk.Frame(self.browser_list_canvas, bg=CARD_BG)
        self.browser_window = self.browser_list_canvas.create_window(
            (0, 0),
            window=self.browser_list_frame,
            anchor="nw",
        )

        self.browser_list_frame.bind("<Configure>", self._on_browser_frame_configure)
        self.browser_list_canvas.bind("<Configure>", self._on_browser_canvas_configure)

        self.selected_label_var = tk.StringVar(value="Đang chọn: chưa có")
        tk.Label(
            self.right_card,
            textvariable=self.selected_label_var,
            bg=CARD_BG,
            fg=SUCCESS,
            font=("Segoe UI Semibold", 10),
            anchor="w",
        ).grid(row=3, column=0, sticky="ew", padx=18, pady=(10, 18))

        if not self.detected_browsers:
            tk.Label(
                self.browser_list_frame,
                text="Không tìm thấy trình duyệt hợp lệ trong máy.",
                bg=CARD_BG,
                fg=TEXT_SUB,
                font=("Segoe UI", 10),
                justify="left",
                wraplength=220,
            ).pack(anchor="w", pady=(8, 0))

    def _make_action_button(self, parent, text, command):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=CARD_BG_2,
            fg=TEXT_MAIN,
            activebackground="#334155",
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI Semibold", 10),
            padx=16,
            pady=10,
            cursor="hand2",
        )

    def _on_browser_frame_configure(self, _event=None):
        self.browser_list_canvas.configure(scrollregion=self.browser_list_canvas.bbox("all"))

    def _on_browser_canvas_configure(self, event):
        self.browser_list_canvas.itemconfig(self.browser_window, width=event.width)

    def _populate_browsers(self):
        for browser in self.detected_browsers:
            name = browser["name"]
            is_default = browser.get("is_default", False)

            card = tk.Frame(
                self.browser_list_frame,
                bg=CARD_BG_2,
                highlightbackground=BORDER,
                highlightthickness=1,
                bd=0,
                cursor="hand2",
            )
            card.pack(fill="x", pady=6)

            card.bind("<Button-1>", lambda e, b=browser: self.select_browser(b["name"]))

            fallback_text = name[0].upper()

            icon_box = tk.Frame(
                card,
                bg=CARD_BG_2,
                width=ICON_BOX_SIZE,
                height=ICON_BOX_SIZE,
                bd=0,
                highlightthickness=0,
            )
            icon_box.pack(side="left", padx=(12, 10), pady=10)
            icon_box.pack_propagate(False)
            icon_box.bind("<Button-1>", lambda e, b=browser: self.select_browser(b["name"]))

            icon_label = tk.Label(
                icon_box,
                text=fallback_text,
                bg=CARD_BG_2,
                fg=TEXT_SUB,
                font=("Segoe UI Semibold", 12),
                bd=0,
                highlightthickness=0,
            )
            icon_label.pack(expand=True)
            icon_label.bind("<Button-1>", lambda e, b=browser: self.select_browser(b["name"]))

            text_frame = tk.Frame(card, bg=CARD_BG_2)
            text_frame.pack(side="left", fill="both", expand=True, pady=10, padx=(0, 10))

            title = name + ("  [default]" if is_default else "")
            title_label = tk.Label(
                text_frame,
                text=title,
                bg=CARD_BG_2,
                fg=TEXT_MAIN,
                font=("Segoe UI Semibold", 10),
                anchor="w",
            )
            title_label.pack(fill="x")
            title_label.bind("<Button-1>", lambda e, b=browser: self.select_browser(b["name"]))

            path_label = tk.Label(
                text_frame,
                text=browser["path"],
                bg=CARD_BG_2,
                fg=TEXT_SUB,
                font=("Segoe UI", 8),
                anchor="w",
                justify="left",
                wraplength=180,
            )
            path_label.pack(fill="x", pady=(4, 0))
            path_label.bind("<Button-1>", lambda e, b=browser: self.select_browser(b["name"]))

            self.browser_buttons[name] = {
                "frame": card,
                "icon_box": icon_box,
                "icon_label": icon_label,
                "title_label": title_label,
                "path_label": path_label,
                "browser": browser,
            }

    def _auto_select_default(self):
        default_name = self.detected_data.get("default_browser_name")
        names = [b["name"] for b in self.detected_browsers]

        if default_name and default_name in names:
            self.select_browser(default_name)
        elif names:
            self.select_browser(names[0])

    def _load_local_logos(self):
        for browser in self.detected_browsers:
            name = browser["name"]
            logo_path = BROWSER_LOGOS.get(name)
            if not logo_path:
                continue

            image = self._load_image_file(logo_path, size=(ICON_IMAGE_SIZE, ICON_IMAGE_SIZE))
            if image:
                self._apply_logo(name, image)

    def _load_image_file(self, file_path, size=(ICON_IMAGE_SIZE, ICON_IMAGE_SIZE)):
        try:
            image = Image.open(file_path).convert("RGBA")
            image = ImageOps.contain(image, size, Image.LANCZOS)

            composed = Image.new("RGBA", (ICON_BOX_SIZE, ICON_BOX_SIZE), (0, 0, 0, 0))
            x = (ICON_BOX_SIZE - image.width) // 2
            y = (ICON_BOX_SIZE - image.height) // 2
            composed.paste(image, (x, y), image)

            return ImageTk.PhotoImage(composed)
        except Exception:
            return None

    def _apply_logo(self, browser_name, image):
        if browser_name not in self.browser_buttons:
            return

        self.logo_images[browser_name] = image
        self.browser_buttons[browser_name]["icon_label"].configure(
            image=image,
            text="",
            width=ICON_BOX_SIZE,
            height=ICON_BOX_SIZE,
        )

    def select_browser(self, browser_name):
        self.selected_browser = browser_name
        self.selected_label_var.set(f"Đang chọn: {browser_name}")

        for name, widgets in self.browser_buttons.items():
            selected = name == browser_name
            bg = ACCENT if selected else CARD_BG_2
            border = SELECT_BORDER if selected else BORDER

            widgets["frame"].configure(bg=bg, highlightbackground=border)
            widgets["icon_box"].configure(bg=bg)
            widgets["icon_label"].configure(bg=bg)
            widgets["title_label"].configure(bg=bg)
            widgets["path_label"].configure(bg=bg)

    def paste_from_clipboard(self):
        try:
            data = self.clipboard_get()
        except tk.TclError:
            data = ""

        if data:
            current = self.textbox.get("1.0", "end-1c").strip()
            if current:
                self.textbox.insert("end", "\n" + data)
            else:
                self.textbox.insert("1.0", data)
            self.update_link_count()

    def clear_text(self):
        self.textbox.delete("1.0", "end")
        self.update_link_count()

    def _on_text_change(self, _event=None):
        self.textbox.edit_modified(False)
        self.update_link_count()

    def update_link_count(self):
        valid_links, invalid_links = analyze_links(self.textbox.get("1.0", "end-1c"))
        self.link_count_var.set(f"Số link hợp lệ: {len(valid_links)}")

        if invalid_links:
            self.link_note_var.set(
                f"Ghi chú: có {len(invalid_links)} link không hợp lệ. App sẽ bỏ qua khi mở."
            )
        else:
            self.link_note_var.set("")

    def open_links(self):
        if not self.selected_browser:
            show_pretty_notice(
                self,
                "warning",
                "Chưa chọn trình duyệt",
                "⚠️",
                f"{AUTHOR_NAME} nhắc bạn hãy chọn một trình duyệt trước khi mở link nhé.",
                self.app_icon_photo,
            )
            return

        valid_links, invalid_links = analyze_links(self.textbox.get("1.0", "end-1c"))

        if not valid_links:
            if invalid_links:
                show_pretty_notice(
                    self,
                    "warning",
                    "Không có link Meet hợp lệ",
                    "🔎",
                    (
                        f"{AUTHOR_NAME} đã kiểm tra nhưng không thấy link Google Meet hợp lệ.\n\n"
                        f"Có {len(invalid_links)} link không hợp lệ và đã bị bỏ qua."
                    ),
                    self.app_icon_photo,
                )
            else:
                show_pretty_notice(
                    self,
                    "warning",
                    "Chưa có link hợp lệ",
                    "🔗",
                    f"{AUTHOR_NAME} chưa tìm thấy link hợp lệ trong ô nhập. Hãy dán link Google Meet rồi thử lại.",
                    self.app_icon_photo,
                )
            return

        browser_info = next((b for b in self.detected_browsers if b["name"] == self.selected_browser), None)
        if not browser_info:
            show_pretty_notice(
                self,
                "error",
                "Không tìm thấy trình duyệt",
                "❌",
                f"{AUTHOR_NAME} không tìm thấy đường dẫn của trình duyệt đã chọn trong máy hiện tại.",
                self.app_icon_photo,
            )
            return

        browser_path = browser_info["path"]
        failed = []

        for idx, link in enumerate(valid_links):
            try:
                subprocess.Popen([browser_path, link], shell=False)
                if idx < len(valid_links) - 1:
                    time.sleep(0.6)
            except Exception:
                failed.append(link)

        opened_count = len(valid_links) - len(failed)
        invalid_note = f"\nĐã bỏ qua {len(invalid_links)} link không hợp lệ." if invalid_links else ""

        if failed:
            show_pretty_notice(
                self,
                "warning",
                "Mở chưa hoàn tất",
                "🌼",
                (
                    f"{AUTHOR_NAME} cảm ơn bạn đã mở link.\n\n"
                    f"Đã mở thành công {opened_count}/{len(valid_links)} link bằng {self.selected_browser}.\n"
                    f"Một số link chưa mở được.{invalid_note}"
                ),
                self.app_icon_photo,
            )
        else:
            show_pretty_notice(
                self,
                "success",
                "Mở link thành công",
                "💖",
                (
                    f"{AUTHOR_NAME} cảm ơn bạn đã mở link.\n\n"
                    f"Đã mở thành công {opened_count} link bằng {self.selected_browser}.{invalid_note}\n"
                    f"Chúc bạn vào Meet thuận lợi ✨"
                ),
                self.app_icon_photo,
            )

    def open_scan_image_window(self):
        self.scan_window_manager.open()

    def _on_window_resize(self, _event=None):
        if self._window_resize_job is not None:
            self.after_cancel(self._window_resize_job)
        self._window_resize_job = self.after(80, self._apply_responsive_layout)

    def _apply_responsive_layout(self):
        self._window_resize_job = None

        right_width = max(self.right_card.winfo_width(), 260)
        wrap = max(140, right_width - 115)

        for widgets in self.browser_buttons.values():
            widgets["path_label"].configure(wraplength=wrap)

        self.default_browser_label.configure(wraplength=max(180, right_width - 36))

        left_width = max(self.left_card.winfo_width(), 500)
        self.link_note_label.configure(wraplength=max(280, left_width - 360))

        total_w = self.winfo_width()
        if total_w < 1180:
            self.open_button.configure(width=20, padx=16)
        else:
            self.open_button.configure(width=18, padx=22)