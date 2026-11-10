import tkinter as tk
import generator, analyzer, recommendations

APP_NAME, FONT, MONO = "SecurePass", "Segoe UI", "Consolas"
C = {
    "navy": "#0B1437", "navy_dark": "#070E29", "navy_light": "#1A2658",
    "bg": "#F3F5FB", "card": "#FFFFFF", "border": "#E1E5F0",
    "text": "#1B2559", "muted": "#6B7599", "field": "#F7F8FD",
    "accent": "#6C4DF6", "accent_dark": "#5A3DE0", "blue": "#3B82F6",
    "green": "#16A34A", "orange": "#F59E0B", "red": "#DC2626", "track": "#E6E9F5",
}
LEVEL_COLORS = {"Very Weak": "#D32F2F", "Weak": "#E8590C", "Moderate": "#F59E0B", "Strong": "#22A559", "Very Strong": "#0E8F4E"}
TOAST = {"success": ("#16A34A", "✔"), "error": ("#DC2626", "✖"), "warning": ("#D97706", "⚠"), "info": ("#4F46E5", "ℹ")}
BTN_THEMES = {
    "primary": (C["accent"], "white", C["accent_dark"]), "danger": ("#FDE8E8", C["red"], "#FBD5D5"),
    "light": ("white", C["navy"], "#E9ECF8"), "secondary": ("#E9ECF8", C["text"], "#D9DDF0"),
}
MAX_ANALYZE_LENGTH, MAX_HISTORY, CLIPBOARD_CLEAR_SECONDS = 128, 10, 30
DEFAULT_SECURE_MODE, METER_HEIGHT, ANALYZER_METER_WIDTH, GENERATOR_METER_WIDTH = False, 16, 440, 300
PATTERN_NEUTRAL = ["No repeated characters", "No predictable sequences", "Not a common password or word"]

root = tk.Tk()
root.title("SecurePass – Password Generator & Strength Analyzer")
root.configure(bg=C["bg"]); root.minsize(1060, 680)
win_x = max(0, (root.winfo_screenwidth() - 1150) // 2)
win_y = max(0, (root.winfo_screenheight() - 720) // 2 - 20)
root.geometry(f"1150x720+{win_x}+{win_y}")

length_var = tk.IntVar(value=generator.DEFAULT_LENGTH)
upper_var, lower_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
digits_var, special_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
exclude_var, secure_var = tk.BooleanVar(value=False), tk.BooleanVar(value=DEFAULT_SECURE_MODE)
history_var, clipboard_var = tk.BooleanVar(value=True), tk.BooleanVar(value=True)
generated_var, password_var = tk.StringVar(value=""), tk.StringVar(value="")
settings_length_var = tk.StringVar(value=str(generator.DEFAULT_LENGTH))

state = {
    "generated": "", "last_settings": None, "history": [], "last_result": None,
    "generated_count": 0, "analyzed_count": 0, "show_password": False,
    "toast_job": None, "clip_job": None, "last_copied": "",
}
w, pages, nav_buttons = {}, {}, {}

def make_card(parent):
    return tk.Frame(parent, bg=C["card"], highlightbackground=C["border"], highlightthickness=1)

def make_label(parent, text, size=10, bold=False, color=None, bg=None, **extra):
    return tk.Label(parent, text=text, font=(FONT, size, "bold" if bold else "normal"),
                    fg=color or C["text"], bg=bg or C["card"], **extra)

def make_button(parent, text, command, kind="primary"):
    bg, fg, active = BTN_THEMES.get(kind, BTN_THEMES["secondary"])
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg, activebackground=active,
                     activeforeground=fg, relief="flat", bd=0, font=(FONT, 10, "bold"), cursor="hand2",
                     padx=14, pady=8, highlightthickness=0)

def make_check(parent, text, variable, command=None):
    return tk.Checkbutton(parent, text=text, variable=variable, command=command, bg=C["card"], fg=C["text"],
                          activebackground=C["card"], activeforeground=C["text"], selectcolor="white",
                          font=(FONT, 10), anchor="w", cursor="hand2", highlightthickness=0)

def make_btn_row(parent, buttons, pady=14):
    row = tk.Frame(parent, bg=C["card"]); row.pack(fill="x", padx=20, pady=pady)
    for i, (txt, cmd, kind) in enumerate(buttons):
        make_button(row, txt, cmd, kind).pack(side="left", padx=(8 if i else 0, 0))
    return row

def make_page_header(page, title, subtitle):
    make_label(page, title, 20, True, bg=C["bg"], anchor="w").pack(fill="x")
    make_label(page, subtitle, 10, False, C["muted"], C["bg"], anchor="w").pack(fill="x", pady=(0, 14))

def make_stat_block(parent, caption):
    box = tk.Frame(parent, bg=C["card"]); box.pack(side="left", expand=True, fill="x", padx=12, pady=12)
    val = make_label(box, "–", 20, True, anchor="w"); val.pack(fill="x")
    make_label(box, caption, 9, color=C["muted"], anchor="w").pack(fill="x")
    return val

def make_checklist(parent, items):
    icons, texts = [], []
    for t in items:
        row = tk.Frame(parent, bg=C["card"]); row.pack(fill="x", padx=20, pady=3)
        icon = make_label(row, "○", 12, True, C["muted"], width=2); icon.pack(side="left")
        text = make_label(row, t, anchor="w", justify="left", wraplength=270); text.pack(side="left")
        icons.append(icon); texts.append(text)
    tk.Frame(parent, bg=C["card"], height=10).pack()
    return icons, texts

def draw_meter(canvas, width, score, color):
    canvas.delete("all")
    w_actual = canvas.winfo_width() if canvas.winfo_width() > 10 else width
    canvas.create_rectangle(0, 0, w_actual, METER_HEIGHT, fill=C["track"], outline="")
    if score > 0:
        canvas.create_rectangle(0, 0, int(w_actual * score / 100), METER_HEIGHT, fill=color, outline="")
    for mark in [25, 45, 65, 85]:
        canvas.create_line(int(w_actual * mark / 100), 0, int(w_actual * mark / 100), METER_HEIGHT, fill="white", width=2)

def hide_toast():
    w["toast"].place_forget(); state["toast_job"] = None

def notify(message, kind="info"):
    bg, icon = TOAST[kind]
    w["toast"].config(text=f"{icon}  {message}", bg=bg)
    w["toast"].place(relx=1.0, rely=1.0, anchor="se", x=-24, y=-24); w["toast"].lift()
    if state["toast_job"] is not None: root.after_cancel(state["toast_job"])
    state["toast_job"] = root.after(4000, hide_toast)

def clear_clipboard_if_ours():
    if state["last_copied"]:
        try:
            if root.clipboard_get() == state["last_copied"]: root.clipboard_clear()
        except tk.TclError: pass
    state["last_copied"], state["clip_job"] = "", None

def copy_text(text, what):
    if not text: return notify("There is nothing to copy yet.", "warning")
    try: root.clipboard_clear(); root.clipboard_append(text); root.update()
    except tk.TclError: return notify("Clipboard is not available. Please copy the text manually.", "error")
    state["last_copied"] = text
    if state["clip_job"] is not None: root.after_cancel(state["clip_job"]); state["clip_job"] = None
    if clipboard_var.get():
        state["clip_job"] = root.after(CLIPBOARD_CLEAR_SECONDS * 1000, clear_clipboard_if_ours)
        notify(f"{what} copied. Clipboard clears in {CLIPBOARD_CLEAR_SECONDS} seconds.", "success")
    else: notify(f"{what} copied to the clipboard.", "success")

def build_dashboard(parent):
    p = tk.Frame(parent, bg=C["bg"])
    make_page_header(p, "Dashboard", "Your security overview for this session")
    banner = tk.Frame(p, bg=C["navy"]); banner.pack(fill="x", pady=(0, 14))
    make_label(banner, "Create strong passwords. Find weak ones.", 17, True, "white", C["navy"], anchor="w").pack(fill="x", padx=24, pady=(18, 2))
    make_label(banner, "Generate random passwords, check how strong your existing ones are, and learn how to improve them.", 10, False, "#B8C1E8", C["navy"], anchor="w").pack(fill="x", padx=24, pady=(0, 12))
    make_btn_row(banner, [("🔑  Generate a Password", lambda: show_page("generator"), "primary"),
                          ("🔍  Analyze a Password", lambda: show_page("analyzer"), "light")], (0, 18))
    stats = tk.Frame(p, bg=C["bg"]); stats.pack(fill="x", pady=(0, 14))
    for i, (k, caption) in enumerate([("stat_generated", "Passwords generated (this session)"),
                                      ("stat_analyzed", "Passwords analyzed (this session)"),
                                      ("stat_last", "Strength of last analysis")]):
        stats.columnconfigure(i, weight=1)
        c = make_card(stats); c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0 if i == 2 else 7))
        w[k] = make_stat_block(c, caption)
    tips = make_card(p); tips.pack(fill="both", expand=True)
    make_label(tips, "Security essentials", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 6))
    for tip in recommendations.GENERAL_TIPS:
        make_label(tips, f"✔  {tip}", 10, anchor="w", justify="left", wraplength=760).pack(fill="x", padx=20, pady=2)
    make_label(tips, "🔒  SecurePass works fully offline. Passwords are kept in memory only and are wiped when you close the app.",
               9, False, C["muted"], anchor="w", justify="left", wraplength=760).pack(fill="x", padx=20, pady=(10, 16))
    return p

def build_generator(parent):
    p = tk.Frame(parent, bg=C["bg"])
    make_page_header(p, "Password Generator", "Create random passwords with the rules you choose")
    b = tk.Frame(p, bg=C["bg"]); b.pack(fill="both", expand=True)
    b.columnconfigure(0, weight=2); b.columnconfigure(1, weight=3); b.rowconfigure(0, weight=1)

    left = make_card(b); left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    make_label(left, "Settings", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 8))
    lrow = tk.Frame(left, bg=C["card"]); lrow.pack(fill="x", padx=20)
    make_label(lrow, "Password length", anchor="w").pack(side="left")
    w["length_label"] = make_label(lrow, f"{generator.DEFAULT_LENGTH} characters", bold=True, color=C["accent"])
    w["length_label"].pack(side="right")
    tk.Scale(left, from_=generator.MIN_LENGTH, to=generator.MAX_LENGTH, orient="horizontal",
             variable=length_var, showvalue=False, command=on_length_change, bg=C["card"],
             troughcolor=C["track"], highlightthickness=0, bd=0, activebackground=C["accent"],
             sliderlength=22, width=14, cursor="hand2").pack(fill="x", padx=20, pady=(2, 10))
    for text, var, pady in [("Uppercase letters (A-Z)", upper_var, 0), ("Lowercase letters (a-z)", lower_var, 0),
                            ("Numbers (0-9)", digits_var, 0), ("Special characters (!@#$%...)", special_var, 0),
                            ("Exclude look-alikes (O, 0, I, l)", exclude_var, (8, 0))]:
        make_check(left, text, var).pack(fill="x", padx=18, pady=pady)
    tk.Frame(left, bg=C["border"], height=1).pack(fill="x", padx=20, pady=12)
    make_check(left, "Secure mode (secrets module)", secure_var, update_mode_label).pack(fill="x", padx=18)
    w["mode_badge"] = tk.Label(left, text="", font=(FONT, 9, "bold"), justify="left", wraplength=250, padx=10, pady=6, anchor="w")
    w["mode_badge"].pack(fill="x", padx=20, pady=(8, 4))
    make_label(left, "Standard mode uses Python's random module: fine for learning, but NOT cryptographically secure. Turn on Secure mode for passwords you will really use.",
               9, False, C["muted"], anchor="w", justify="left", wraplength=250).pack(fill="x", padx=20, pady=(0, 16))

    right = tk.Frame(b, bg=C["bg"]); right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
    out = make_card(right); out.pack(fill="x")
    make_label(out, "Your password", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 8))
    tk.Entry(out, textvariable=generated_var, state="readonly", readonlybackground=C["field"], fg=C["text"],
             font=(MONO, 16), relief="flat", highlightthickness=1, highlightbackground=C["border"]).pack(fill="x", padx=20, ipady=10)
    mrow = tk.Frame(out, bg=C["card"]); mrow.pack(fill="x", padx=20, pady=(12, 0))
    w["gen_meter"] = tk.Canvas(mrow, width=GENERATOR_METER_WIDTH, height=METER_HEIGHT, bg=C["track"], highlightthickness=0)
    w["gen_meter"].pack(side="left")
    w["gen_strength"] = make_label(mrow, "Strength: –", bold=True, color=C["muted"]); w["gen_strength"].pack(side="left", padx=12)
    make_btn_row(out, [("⚡  Generate Password", generate_click, "primary"), ("↻  Regenerate", regenerate_click, "secondary"),
                       ("⧉  Copy Password", lambda: copy_text(state["generated"], "Password"), "secondary")])
    make_label(out, "⚠  Never reuse a password on more than one account.", 9, False, "#B45309", anchor="w").pack(fill="x", padx=20, pady=(0, 14))

    hist = make_card(right); hist.pack(fill="both", expand=True, pady=(14, 0))
    make_label(hist, "Session history", 12, True, anchor="w").pack(fill="x", padx=20, pady=(14, 6))
    w["history_list"] = tk.Listbox(hist, height=5, font=(MONO, 11), bg=C["field"], fg=C["text"], relief="flat",
                                   highlightthickness=1, highlightbackground=C["border"], selectbackground=C["accent"],
                                   selectforeground="white", activestyle="none", exportselection=False)
    w["history_list"].pack(fill="both", expand=True, padx=20)
    make_btn_row(hist, [("Copy Selected", copy_history_click, "secondary"), ("Clear History", clear_history_click, "danger")], (10, 4))
    make_label(hist, "Kept in memory only and erased when you close SecurePass.", 9, False, C["muted"], anchor="w").pack(fill="x", padx=20, pady=(0, 12))
    return p

def build_analyzer(parent):
    p = tk.Frame(parent, bg=C["bg"])
    make_page_header(p, "Password Strength Analyzer", "Check a password against security requirements")
    b = tk.Frame(p, bg=C["bg"]); b.pack(fill="both", expand=True)
    b.columnconfigure(0, weight=3); b.columnconfigure(1, weight=2); b.rowconfigure(0, weight=1)

    left = tk.Frame(b, bg=C["bg"]); left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    ecard = make_card(left); ecard.pack(fill="x")
    make_label(ecard, "Enter a password to analyze", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 8))
    erow = tk.Frame(ecard, bg=C["card"]); erow.pack(fill="x", padx=20)
    w["password_entry"] = tk.Entry(erow, textvariable=password_var, show="•", font=(MONO, 14), relief="flat",
                                   bg=C["field"], fg=C["text"], insertbackground=C["text"],
                                   highlightthickness=1, highlightbackground=C["border"], highlightcolor=C["accent"])
    w["password_entry"].pack(side="left", fill="x", expand=True, ipady=8)
    w["password_entry"].bind("<Return>", lambda e: analyze_click())
    w["show_button"] = make_button(erow, "👁  Show", toggle_visibility, "secondary"); w["show_button"].pack(side="left", padx=(8, 0))
    make_btn_row(ecard, [("🔍  Analyze Password", analyze_click, "primary"),
                         ("⧉  Copy", lambda: copy_text(password_var.get(), "Password"), "secondary"),
                         ("✖  Clear", clear_analyzer_click, "danger")])

    rcard = make_card(left); rcard.pack(fill="both", expand=True, pady=(14, 0))
    trow = tk.Frame(rcard, bg=C["card"]); trow.pack(fill="x", padx=20, pady=(16, 8))
    w["result_label"] = make_label(trow, "No analysis yet", 18, True, color=C["muted"]); w["result_label"].pack(side="left")
    w["score_label"] = make_label(trow, "– / 100", 14, True, color=C["muted"]); w["score_label"].pack(side="right")
    w["meter"] = tk.Canvas(rcard, width=ANALYZER_METER_WIDTH, height=METER_HEIGHT, bg=C["track"], highlightthickness=0); w["meter"].pack(fill="x", padx=20)
    srow = tk.Frame(rcard, bg=C["card"]); srow.pack(fill="x", padx=8, pady=(6, 0))
    w["length_value"] = make_stat_block(srow, "Password length")
    w["met_value"] = make_stat_block(srow, "Requirements met")
    w["missing_label"] = make_label(rcard, "", 10, anchor="w", justify="left", wraplength=440); w["missing_label"].pack(fill="x", padx=20, pady=(0, 6))
    make_label(rcard, "ℹ  The score is an educational heuristic, not a guarantee that a password is secure.",
               9, False, C["muted"], anchor="w", justify="left", wraplength=440).pack(fill="x", padx=20, pady=(0, 14))

    right = tk.Frame(b, bg=C["bg"]); right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
    ccard = make_card(right); ccard.pack(fill="x")
    make_label(ccard, "Requirement checklist", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 8))
    w["req_icons"], w["req_texts"] = make_checklist(ccard, [r[0] for r in analyzer.analyze_password("")["requirements"]])
    pcard = make_card(right); pcard.pack(fill="x", pady=(14, 0))
    make_label(pcard, "Pattern checks", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 8))
    w["pat_icons"], w["pat_texts"] = make_checklist(pcard, PATTERN_NEUTRAL)
    make_button(right, "💡  View Recommendations  →", lambda: show_page("recommendations"), "secondary").pack(fill="x", pady=(14, 0))
    return p

def add_rec_row(parent, icon, color, text):
    row = tk.Frame(parent, bg=C["card"]); row.pack(fill="x", padx=20, pady=3)
    make_label(row, icon, 11, True, color, width=2, anchor="n").pack(side="left", anchor="n")
    make_label(row, text, anchor="w", justify="left", wraplength=700).pack(side="left", fill="x")

def build_recommendations(parent):
    p = tk.Frame(parent, bg=C["bg"])
    make_page_header(p, "Security Recommendations", "Advice based on the last password you analyzed")
    c1 = make_card(p); c1.pack(fill="x")
    make_label(c1, "Personalised recommendations", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 4))
    w["rec_summary"] = make_label(c1, "", 10, True, anchor="w"); w["rec_summary"].pack(fill="x", padx=20, pady=(0, 6))
    w["rec_list"] = tk.Frame(c1, bg=C["card"]); w["rec_list"].pack(fill="x", padx=20, pady=(0, 14))
    c2 = make_card(p); c2.pack(fill="x", pady=(14, 0))
    make_label(c2, "Good habits for every account", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 6))
    for tip in recommendations.GENERAL_TIPS: add_rec_row(c2, "✔", C["blue"], tip)
    tk.Frame(c2, bg=C["card"], height=10).pack()
    return p

def build_settings(parent):
    p = tk.Frame(parent, bg=C["bg"])
    make_page_header(p, "Settings", "Customise generation preferences and privacy options")
    b = tk.Frame(p, bg=C["bg"]); b.pack(fill="both", expand=True)
    b.columnconfigure(0, weight=1); b.columnconfigure(1, weight=1)

    gen = make_card(b); gen.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
    make_label(gen, "Generation preferences", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 8))
    row = tk.Frame(gen, bg=C["card"]); row.pack(fill="x", padx=20, pady=(0, 6))
    make_label(row, "Default password length", anchor="w").pack(side="left")
    make_button(row, "Apply", apply_default_length, "secondary").pack(side="right")
    tk.Spinbox(row, from_=generator.MIN_LENGTH, to=generator.MAX_LENGTH, textvariable=settings_length_var, width=5, font=(FONT, 11), justify="center").pack(side="right", padx=8)
    make_check(gen, "Exclude look-alikes (O, 0, I, l)", exclude_var).pack(fill="x", padx=18)
    make_check(gen, "Secure mode (secrets module)", secure_var, update_mode_label).pack(fill="x", padx=18)
    make_label(gen, f"Allowed length: {generator.MIN_LENGTH} to {generator.MAX_LENGTH} characters. Character types are chosen on the Generator page.",
               9, False, C["muted"], anchor="w", justify="left", wraplength=380).pack(fill="x", padx=20, pady=(8, 16))

    priv = make_card(b); priv.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
    make_label(priv, "Privacy & session", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 8))
    make_check(priv, "Keep a temporary history of generated passwords", history_var, on_history_toggle).pack(fill="x", padx=18)
    make_check(priv, f"Auto-clear clipboard after {CLIPBOARD_CLEAR_SECONDS} seconds", clipboard_var).pack(fill="x", padx=18)
    make_btn_row(priv, [("Reset to Defaults", reset_settings_click, "secondary"), ("Clear All Session Data", clear_session_click, "danger")], (14, 16))

    about = make_card(b); about.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(14, 0))
    make_label(about, "About SecurePass", 12, True, anchor="w").pack(fill="x", padx=20, pady=(16, 6))
    for note in ["Passwords are never saved to disk, printed, or sent anywhere.",
                 "Strength scores are an educational heuristic, not a security guarantee.",
                 "Python's random module is not cryptographically secure; Secure mode uses the secrets module instead.",
                 "Python cannot fully erase text from memory, so close SecurePass when you are finished."]:
        make_label(about, f"•  {note}", 10, False, anchor="w", justify="left", wraplength=900).pack(fill="x", padx=20, pady=2)
    tk.Frame(about, bg=C["card"], height=12).pack()
    return p

def build_header(parent):
    h = tk.Frame(parent, bg=C["navy_dark"], height=64); h.pack(fill="x"); h.pack_propagate(False)
    logo = tk.Canvas(h, width=40, height=40, bg=C["navy_dark"], highlightthickness=0); logo.pack(side="left", padx=(22, 10), pady=12)
    logo.create_polygon(20, 2, 36, 8, 36, 21, 20, 38, 4, 21, 4, 8, fill=C["accent"], outline="")
    logo.create_oval(15, 12, 25, 22, fill="white", outline=""); logo.create_rectangle(18, 20, 22, 29, fill="white", outline="")
    make_label(h, "SecurePass", 18, True, "white", C["navy_dark"]).pack(side="left")
    make_label(h, "Password Generator & Strength Analyzer", 10, False, "#8E9AD0", C["navy_dark"]).pack(side="left", padx=14, pady=(6, 0))
    make_label(h, "●  Offline · nothing is saved or sent", 9, True, "#4ADE80", C["navy_dark"]).pack(side="right", padx=22)

def build_sidebar(parent):
    s = tk.Frame(parent, bg=C["navy"], width=225); s.pack(side="left", fill="y"); s.pack_propagate(False)
    make_label(s, "MENU", 9, True, "#6F7BB0", C["navy"], anchor="w").pack(fill="x", padx=22, pady=(22, 8))
    for name, text in [("dashboard", "🏠   Dashboard"), ("generator", "🔑   Password Generator"),
                       ("analyzer", "🔍   Strength Analyzer"), ("recommendations", "💡   Recommendations"),
                       ("settings", "⚙   Settings")]:
        btn = tk.Button(s, text=text, command=lambda n=name: show_page(n), anchor="w",
                        bg=C["navy"], fg="#C9D1F2", activebackground=C["navy_light"], activeforeground="white",
                        relief="flat", bd=0, font=(FONT, 11), cursor="hand2", padx=22, pady=12, highlightthickness=0)
        btn.pack(fill="x"); nav_buttons[name] = btn
    make_label(s, "Session data is erased\nwhen you close the app.", 9, False, "#6F7BB0", C["navy"], justify="left").pack(side="bottom", anchor="w", padx=22, pady=18)

def show_page(name):
    for p in pages.values(): p.pack_forget()
    pages[name].pack(fill="both", expand=True, padx=28, pady=22)
    for btn_name, btn in nav_buttons.items():
        btn.config(bg=C["navy_light"] if btn_name == name else C["navy"], fg="white" if btn_name == name else "#C9D1F2")
    if name == "dashboard": refresh_dashboard()
    elif name == "recommendations": refresh_recommendations()

def refresh_dashboard():
    w["stat_generated"].config(text=str(state["generated_count"]))
    w["stat_analyzed"].config(text=str(state["analyzed_count"]))
    res = state["last_result"]
    w["stat_last"].config(text="–" if not res else res["label"], fg=C["muted"] if not res else LEVEL_COLORS[res["label"]])

def refresh_recommendations():
    for child in w["rec_list"].winfo_children(): child.destroy()
    res = state["last_result"]
    if not res:
        w["rec_summary"].config(text="No password analyzed yet.", fg=C["muted"])
        return add_rec_row(w["rec_list"], "ℹ", C["blue"], "Open the Strength Analyzer, enter a password and click Analyze Password. Tailored advice will appear here.")
    w["rec_summary"].config(text=f"Last analysis: {res['label']} ({res['score']} / 100)", fg=LEVEL_COLORS[res["label"]])
    for advice in recommendations.get_recommendations(res): add_rec_row(w["rec_list"], "⚠", C["orange"], advice)

def on_length_change(value):
    w["length_label"].config(text=f"{int(float(value))} characters")

def update_mode_label():
    if secure_var.get():
        w["mode_badge"].config(text="🛡  SECURE MODE  ·  secrets module", bg="#DCFCE7", fg="#166534")
    else:
        w["mode_badge"].config(text="STANDARD MODE  ·  random module (educational, not cryptographically secure)", bg="#FEF3C7", fg="#92400E")

def read_length():
    try: return int(length_var.get())
    except tk.TclError: return None

def show_generated_strength(password):
    if not password:
        draw_meter(w["gen_meter"], GENERATOR_METER_WIDTH, 0, C["track"])
        return w["gen_strength"].config(text="Strength: –", fg=C["muted"])
    res = analyzer.analyze_password(password)
    color = LEVEL_COLORS[res["label"]]
    draw_meter(w["gen_meter"], GENERATOR_METER_WIDTH, res["score"], color)
    w["gen_strength"].config(text=f"{res['label']} ({res['score']})", fg=color)

def refresh_history():
    w["history_list"].delete(0, tk.END)
    for item in state["history"]: w["history_list"].insert(tk.END, item)

def run_generation(settings):
    try:
        pw, err = generator.generate_password(
            settings["length"], settings["upper"], settings["lower"],
            settings["digits"], settings["special"], settings["exclude"], settings["secure"])
    except Exception: return notify("Unexpected error while generating. Please try again.", "error")
    if err: return notify(err, "error")
    state["generated"], state["last_settings"] = pw, settings
    state["generated_count"] += 1
    generated_var.set(pw); show_generated_strength(pw)
    if history_var.get():
        state["history"].insert(0, pw); del state["history"][MAX_HISTORY:]; refresh_history()
    notify("New password generated.", "success")

def generate_click():
    run_generation({
        "length": read_length(), "upper": upper_var.get(), "lower": lower_var.get(),
        "digits": digits_var.get(), "special": special_var.get(), "exclude": exclude_var.get(),
        "secure": secure_var.get(),
    })

def regenerate_click():
    run_generation(state["last_settings"]) if state["last_settings"] else generate_click()

def copy_history_click():
    sel = w["history_list"].curselection()
    if not sel: return notify("Select a password in the history list first.", "warning")
    copy_text(state["history"][sel[0]], "Password")

def clear_history_click():
    state["history"].clear(); refresh_history(); notify("History cleared.", "info")

def toggle_visibility():
    state["show_password"] = not state["show_password"]
    w["password_entry"].config(show="" if state["show_password"] else "•")
    w["show_button"].config(text="🙈  Hide" if state["show_password"] else "👁  Show")

def hide_password_field():
    state["show_password"] = False
    w["password_entry"].config(show="•"); w["show_button"].config(text="👁  Show")

def reset_analysis_display():
    w["result_label"].config(text="No analysis yet", fg=C["muted"])
    w["score_label"].config(text="– / 100", fg=C["muted"])
    draw_meter(w["meter"], ANALYZER_METER_WIDTH, 0, C["track"])
    w["length_value"].config(text="–"); w["met_value"].config(text="–")
    w["missing_label"].config(text="Enter a password and click Analyze Password.", fg=C["muted"])
    for (desc, _), ic, tx in zip(analyzer.analyze_password("")["requirements"], w["req_icons"], w["req_texts"]):
        ic.config(text="○", fg=C["muted"]); tx.config(text=desc, fg=C["muted"])
    for pat, ic, tx in zip(PATTERN_NEUTRAL, w["pat_icons"], w["pat_texts"]):
        ic.config(text="○", fg=C["muted"]); tx.config(text=pat, fg=C["muted"])

def set_row(icon_label, text_label, ok, text):
    icon_label.config(text="✔" if ok else "⚠", fg=C["green"] if ok else C["orange"])
    text_label.config(text=text, fg=C["text"])

def show_analysis(result):
    col = LEVEL_COLORS[result["label"]]
    w["result_label"].config(text=result["label"], fg=col)
    w["score_label"].config(text=f"{result['score']} / 100", fg=col)
    draw_meter(w["meter"], ANALYZER_METER_WIDTH, result["score"], col)
    w["length_value"].config(text=str(result["length"]))
    w["met_value"].config(text=f"{result['met_count']} / {result['total_requirements']}")
    for (desc, met), ic, tx in zip(result["requirements"], w["req_icons"], w["req_texts"]):
        set_row(ic, tx, met, desc)
    checks = [
        (result["repeated_run"], PATTERN_NEUTRAL[0], f"Repeated characters found: '{result['repeated_run']}'"),
        (result["sequence"], PATTERN_NEUTRAL[1], f"Predictable sequence found: '{result['sequence']}'"),
        (result["common_word"], PATTERN_NEUTRAL[2], f"Common password/word detected: '{result['common_word']}'"),
    ]
    for (val, neutral, alert), ic, tx in zip(checks, w["pat_icons"], w["pat_texts"]):
        set_row(ic, tx, not val, neutral if not val else alert)
    w["missing_label"].config(text="✔  All listed requirements are met." if not result["missing"] else f"⚠  Missing: {'; '.join(result['missing'])}.",
                              fg=C["green"] if not result["missing"] else "#B45309")

def analyze_click():
    pw = password_var.get()
    if not pw: return notify("Please enter a password to analyze.", "warning")
    if len(pw) > MAX_ANALYZE_LENGTH:
        return notify(f"That password is too long to analyze (maximum {MAX_ANALYZE_LENGTH} characters).", "error")
    try: res = analyzer.analyze_password(pw)
    except Exception: return notify("Unexpected error while analyzing. Please try again.", "error")

    state["last_result"] = res; state["analyzed_count"] += 1; show_analysis(res)
    kind = "success" if res["label"] in ("Strong", "Very Strong") else ("warning" if res["label"] == "Moderate" else "error")
    msg = f"Analysis complete: {res['label']}." if kind == "success" else f"Analysis complete: {res['label']}. See Recommendations."
    notify(msg, kind)

def clear_analyzer_click():
    password_var.set(""); hide_password_field(); reset_analysis_display()
    state["last_result"] = None; notify("Password field and analysis cleared.", "info")

def apply_default_length():
    try: val = int(settings_length_var.get().strip())
    except ValueError: return notify("Default length must be a whole number, e.g. 16.", "error")
    if not (generator.MIN_LENGTH <= val <= generator.MAX_LENGTH):
        return notify(f"Default length must be between {generator.MIN_LENGTH} and {generator.MAX_LENGTH}.", "error")
    length_var.set(val); w["length_label"].config(text=f"{val} characters")
    notify(f"Default length set to {val}.", "success")

def on_history_toggle():
    if not history_var.get():
        state["history"].clear(); refresh_history(); notify("History turned off and cleared.", "info")

def reset_settings_click():
    length_var.set(generator.DEFAULT_LENGTH); settings_length_var.set(str(generator.DEFAULT_LENGTH))
    w["length_label"].config(text=f"{generator.DEFAULT_LENGTH} characters")
    for v, val in [(upper_var, True), (lower_var, True), (digits_var, True), (special_var, True),
                   (exclude_var, False), (secure_var, DEFAULT_SECURE_MODE), (history_var, True), (clipboard_var, True)]:
        v.set(val)
    update_mode_label(); notify("Settings restored to defaults.", "success")

def wipe_session_data():
    state.update({"generated": "", "last_settings": None, "history": [], "last_result": None})
    generated_var.set(""); password_var.set(""); hide_password_field()
    refresh_history(); show_generated_strength(""); reset_analysis_display(); clear_clipboard_if_ours()

def clear_session_click():
    wipe_session_data(); notify("All session data cleared.", "success")

def on_exit():
    wipe_session_data(); root.destroy()

def start_app():
    w["toast"] = tk.Label(root, text="", fg="white", font=(FONT, 10, "bold"), padx=18, pady=10)
    build_header(root)
    body = tk.Frame(root, bg=C["bg"]); body.pack(fill="both", expand=True)
    build_sidebar(body)
    content = tk.Frame(body, bg=C["bg"]); content.pack(side="left", fill="both", expand=True)

    for page_id, builder in [
        ("dashboard", build_dashboard), ("generator", build_generator),
        ("analyzer", build_analyzer), ("recommendations", build_recommendations),
        ("settings", build_settings),
    ]:
        pages[page_id] = builder(content)

    update_mode_label(); show_generated_strength(""); reset_analysis_display(); show_page("dashboard")
    root.protocol("WM_DELETE_WINDOW", on_exit)
    root.mainloop()

if __name__ == "__main__":
    start_app()
