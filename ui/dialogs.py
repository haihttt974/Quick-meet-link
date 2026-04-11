import tkinter as tk

from config import (
    ACCENT,
    APP_BG,
    AUTHOR_NAME,
    BORDER,
    CARD_BG,
    DANGER,
    SUCCESS,
    TEXT_MAIN,
    TEXT_SUB,
    WARNING,
)


def show_pretty_notice(parent, kind: str, title: str, icon: str, message: str, app_icon_photo=None):
    colors = {
        "success": SUCCESS,
        "warning": WARNING,
        "error": DANGER,
    }
    accent = colors.get(kind, ACCENT)

    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=APP_BG)
    win.resizable(False, False)
    win.transient(parent)
    win.grab_set()

    try:
        if app_icon_photo is not None:
            win.iconphoto(True, app_icon_photo)
    except Exception:
        pass

    body = tk.Frame(
        win,
        bg=CARD_BG,
        highlightbackground=BORDER,
        highlightthickness=1,
        bd=0,
    )
    body.pack(fill="both", expand=True, padx=18, pady=18)

    header = tk.Frame(body, bg=CARD_BG)
    header.pack(fill="x", padx=18, pady=(18, 8))

    icon_label = tk.Label(
        header,
        text=icon,
        bg=CARD_BG,
        fg=accent,
        font=("Segoe UI Emoji", 28),
    )
    icon_label.pack(side="left", padx=(0, 10))

    title_wrap = tk.Frame(header, bg=CARD_BG)
    title_wrap.pack(side="left", fill="both", expand=True)

    tk.Label(
        title_wrap,
        text=title,
        bg=CARD_BG,
        fg=TEXT_MAIN,
        font=("Segoe UI Semibold", 14),
        anchor="w",
    ).pack(fill="x")

    tk.Label(
        title_wrap,
        text=f"Từ {AUTHOR_NAME}",
        bg=CARD_BG,
        fg=TEXT_SUB,
        font=("Segoe UI", 9),
        anchor="w",
    ).pack(fill="x", pady=(4, 0))

    line = tk.Frame(body, bg=accent, height=2)
    line.pack(fill="x", padx=18, pady=(0, 12))

    msg = tk.Label(
        body,
        text=message,
        bg=CARD_BG,
        fg=TEXT_MAIN,
        font=("Segoe UI", 10),
        justify="left",
        anchor="w",
        wraplength=420,
    )
    msg.pack(fill="x", padx=18)

    footer = tk.Frame(body, bg=CARD_BG)
    footer.pack(fill="x", padx=18, pady=(18, 18))
    footer.grid_columnconfigure(0, weight=1)

    tk.Label(
        footer,
        text=f"🌷 {AUTHOR_NAME}",
        bg=CARD_BG,
        fg=accent,
        font=("Segoe UI Semibold", 10),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")

    ok_btn = tk.Button(
        footer,
        text="Đóng",
        command=win.destroy,
        bg=accent,
        fg="white",
        activebackground=accent,
        activeforeground="white",
        relief="flat",
        bd=0,
        highlightthickness=0,
        font=("Segoe UI Semibold", 10),
        padx=18,
        pady=8,
        cursor="hand2",
    )
    ok_btn.grid(row=0, column=1, sticky="e")

    win.update_idletasks()
    width = max(500, body.winfo_reqwidth() + 36)
    height = body.winfo_reqheight() + 36

    parent_x = parent.winfo_rootx()
    parent_y = parent.winfo_rooty()
    parent_w = parent.winfo_width()
    parent_h = parent.winfo_height()

    x = parent_x + (parent_w - width) // 2
    y = parent_y + (parent_h - height) // 2

    win.geometry(f"{width}x{height}+{x}+{y}")
    ok_btn.focus_set()
    win.bind("<Return>", lambda _e: win.destroy())
    win.bind("<Escape>", lambda _e: win.destroy())