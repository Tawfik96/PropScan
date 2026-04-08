import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import json
import os
from datetime import datetime
from collections import defaultdict

# ── DPI awareness (Windows only) ─────────────────────────────────────────────
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

# ── Colour palette ──────────────────────────────────────────────────────────
BG         = "#1a1a1f"
PANEL      = "#22222a"
CARD       = "#2a2a35"
BORDER     = "#3a3a48"
ACCENT     = "#7c6af7"
ACCENT2    = "#a08cf8"
GREEN_DIM  = "#1d5c42"
GREEN_FG   = "#3ecf8e"
TEXT       = "#e8e6f0"
TEXT_DIM   = "#8884a0"
TEXT_MUTED = "#55536a"
ENTRY_BG   = "#18181f"
SNIPPET_BG = "#1e1c2e"

FONT_SMALL = ("Segoe UI", 9)
FONT_BODY  = ("Segoe UI", 10)

# ── Field definitions ────────────────────────────────────────────────────────
ENUM_FIELDS = {
    "property_type": ["","apartment","villa","studio","duplex","penthouse","chalet",
                      "townhouse","twin_house","standalone","i_villa","land","office",
                      "shop","warehouse","building","loft","other"],
    "transaction_type": ["","sale","rent","daily_rent"],
    "currency":  ["","EGP","USD","EUR"],
}
BOOL_FIELDS = []
NUM_FIELDS  = ["price","bedrooms"]

FIELD_ORDER = [
    ("property_type","transaction_type","currency","price","bedrooms","compound_name"),
]

LABEL_MAP = {
    "property_type":"Property Type","transaction_type":"Transaction",
    "price":"Price","currency":"Currency","bedrooms":"Bedrooms",
    "compound_name":"Compound","ad_snippet":"Ad Snippet",
    "original_message":"Original Msg",
}

# ── Helpers ──────────────────────────────────────────────────────────────────
def parse_date(val):
    if not val:
        return None
    try:
        return datetime.fromisoformat(str(val)).date()
    except Exception:
        return None

def fmt_date_header(d):
    if d is None:
        return "Unknown Date"
    return d.strftime("%A, %d %b %Y")


def format_price_display(value):
    if value is None or value == "":
        return ""
    try:
        return f"{int(value):_}"
    except Exception:
        return str(value)


def normalize_price_input(raw):
    if raw is None:
        return ""
    return str(raw).replace("_", "").replace(",", "").strip()


def verified_path(db_path):
    return os.path.splitext(db_path)[0] + "_verified.json"

def load_verified(db_path):
    p = verified_path(db_path)
    if os.path.exists(p):
        with open(p) as f:
            return set(json.load(f))
    return set()

def save_verified(db_path, ids):
    with open(verified_path(db_path), "w") as f:
        json.dump(list(ids), f)


# ── Main Application ─────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Real Estate Ad Reviewer")
        self.configure(bg=BG)
        self._size_window()

        self.db_path         = None
        self.conn            = None
        self.table_name      = None
        self.records         = []
        self.current         = None
        self.current_idx     = 0
        self.verified        = set()
        self.sidebar_visible = True
        self.meta_visible    = False
        self.fields_visible  = False
        self._snippet_resize_job = None

        # sidebar item registry  {rec_id: (outer, inner, indicator, top, is_ver, bg, fg)}
        self._sb_items     = {}
        self._active_sb_id = None

        self._build_ui()
        self._apply_ttk_style()
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.after(100, self._open_file_dialog)

    def _size_window(self):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = int(sw * 0.80)
        h  = int(sh * 0.80)
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.minsize(900, 600)

    def _apply_ttk_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TCombobox",
                    fieldbackground=ENTRY_BG, background=ENTRY_BG,
                    foreground=TEXT, selectforeground=TEXT,
                    selectbackground=ACCENT, arrowcolor=TEXT_DIM,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
                    font=FONT_SMALL)
        s.map("TCombobox",
              fieldbackground=[("readonly", ENTRY_BG)],
              foreground=[("readonly", TEXT)])
        self.option_add("*TCombobox*Listbox.background", ENTRY_BG)
        self.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.option_add("*TCombobox*Listbox.selectBackground", ACCENT)

    # ── UI skeleton ───────────────────────────────────────────────────────────
    def _build_ui(self):
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True)
        self._build_topbar(root)
        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        self._build_main(body)

    # ── Top bar ───────────────────────────────────────────────────────────────
    def _build_topbar(self, parent):
        bar = tk.Frame(parent, bg=PANEL, height=46)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        self.sb_toggle_btn = tk.Button(
            bar, text="◀  Sidebar", bg=PANEL, fg=TEXT_DIM,
            relief="flat", bd=0, padx=12, font=FONT_SMALL, cursor="hand2",
            command=self._toggle_sidebar,
            activebackground=CARD, activeforeground=TEXT)
        self.sb_toggle_btn.pack(side="left", pady=8)

        tk.Label(bar, text="RE·REVIEW", bg=PANEL, fg=ACCENT2,
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=8)

        tk.Button(bar, text="📂  Open DB", bg=ACCENT, fg="white",
                  relief="flat", bd=0, padx=14, pady=4, font=FONT_SMALL,
                  cursor="hand2", command=self._open_file_dialog,
                  activebackground=ACCENT2).pack(side="right", padx=10, pady=6)

        self.stats_var = tk.StringVar(value="No file loaded")
        tk.Label(bar, textvariable=self.stats_var, bg=PANEL, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(side="right", padx=16)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, parent):
        self.sidebar_frame = tk.Frame(parent, bg=PANEL, width=260)
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        sr = tk.Frame(self.sidebar_frame, bg=PANEL)
        sr.pack(fill="x", padx=8, pady=(8, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._full_sidebar_rebuild())
        self._search_entry = tk.Entry(
            sr, textvariable=self.search_var,
            bg=ENTRY_BG, fg=TEXT_MUTED, insertbackground=TEXT,
            relief="flat", font=FONT_SMALL, bd=4)
        self._search_entry.pack(fill="x")
        self._search_entry.insert(0, "🔍  search…")
        self._search_entry.bind("<FocusIn>",  self._search_focus_in)
        self._search_entry.bind("<FocusOut>", self._search_focus_out)

        fr = tk.Frame(self.sidebar_frame, bg=PANEL)
        fr.pack(fill="x", padx=8, pady=(0, 6))
        self.filter_var = tk.StringVar(value="all")
        for val, lbl in [("all","All"),("pending","Pending"),("verified","✓ Done")]:
            tk.Radiobutton(
                fr, text=lbl, variable=self.filter_var, value=val,
                bg=PANEL, fg=TEXT_DIM, selectcolor=PANEL,
                activebackground=PANEL, activeforeground=TEXT,
                font=FONT_SMALL, cursor="hand2",
                command=self._full_sidebar_rebuild
            ).pack(side="left", padx=(0, 4))

        tk.Frame(self.sidebar_frame, bg=BORDER, height=1).pack(fill="x")

        container = tk.Frame(self.sidebar_frame, bg=PANEL)
        container.pack(fill="both", expand=True)

        self.sb_canvas = tk.Canvas(container, bg=PANEL,
                                   highlightthickness=0, bd=0)
        sb_scroll = tk.Scrollbar(container, orient="vertical",
                                 command=self.sb_canvas.yview)
        self.sb_canvas.configure(yscrollcommand=sb_scroll.set)
        sb_scroll.pack(side="right", fill="y")
        self.sb_canvas.pack(side="left", fill="both", expand=True)

        self.sb_list = tk.Frame(self.sb_canvas, bg=PANEL)
        self.sb_canvas.create_window((0, 0), window=self.sb_list,
                                     anchor="nw", tags="sblist")
        self.sb_list.bind("<Configure>",
            lambda e: self.sb_canvas.configure(
                scrollregion=self.sb_canvas.bbox("all")))
        self.sb_canvas.bind("<Configure>",
            lambda e: self.sb_canvas.itemconfig("sblist", width=e.width))
        self.sb_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _search_focus_in(self, _e):
        if self._search_entry.get().startswith("🔍"):
            self._search_entry.delete(0, "end")
            self._search_entry.config(fg=TEXT)

    def _search_focus_out(self, _e):
        if not self._search_entry.get():
            self._search_entry.insert(0, "🔍  search…")
            self._search_entry.config(fg=TEXT_MUTED)

    def _on_mousewheel(self, e):
        self.sb_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar_frame.pack_forget()
            self.sb_toggle_btn.config(text="▶  Sidebar")
        else:
            self.sidebar_frame.pack(side="left", fill="y",
                                    before=self.main_frame)
            self.sb_toggle_btn.config(text="◀  Sidebar")
        self.sidebar_visible = not self.sidebar_visible

    # ── Main panel ────────────────────────────────────────────────────────────
    def _build_main(self, parent):
        self.main_frame = tk.Frame(parent, bg=BG)
        self.main_frame.pack(side="left", fill="both", expand=True)

        nav = tk.Frame(self.main_frame, bg=PANEL, height=44)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        self.rec_label = tk.Label(nav, text="—", bg=PANEL, fg=TEXT_DIM,
                                  font=FONT_SMALL)
        self.rec_label.pack(side="left", padx=14)

        bcfg = dict(relief="flat", bd=0, padx=12, pady=4,
                    font=FONT_SMALL, cursor="hand2")
        tk.Button(nav, text="← Prev",  bg=CARD, fg=TEXT,
                  command=self._go_prev,
                  activebackground=BORDER, **bcfg
                  ).pack(side="right", padx=(0, 4), pady=6)
        tk.Button(nav, text="Next →",  bg=CARD, fg=TEXT,
                  command=self._go_next,
                  activebackground=BORDER, **bcfg
                  ).pack(side="right", padx=(0, 4), pady=6)
        tk.Button(nav, text="✓  Save & Next", bg=GREEN_DIM, fg=GREEN_FG,
                  command=self._save_and_next,
                  activebackground="#245c3d", **bcfg
                  ).pack(side="right", padx=(0, 8), pady=6)
        tk.Button(nav, text="💾  Save", bg=ACCENT, fg="white",
                  command=self._save_current,
                  activebackground=ACCENT2, **bcfg
                  ).pack(side="right", padx=(0, 4), pady=6)

        tk.Frame(self.main_frame, bg=BORDER, height=1).pack(fill="x")

        outer = tk.Frame(self.main_frame, bg=BG)
        outer.pack(fill="both", expand=True)

        self.main_canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, bd=0)
        ms = tk.Scrollbar(outer, orient="vertical",
                          command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=ms.set)
        ms.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)

        self.content_frame = tk.Frame(self.main_canvas, bg=BG)
        self.main_canvas.create_window((0, 0), window=self.content_frame,
                                       anchor="nw", tags="cf")
        self.content_frame.bind("<Configure>",
            lambda e: self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all")))
        self.main_canvas.bind("<Configure>",
            lambda e: self.main_canvas.itemconfig("cf", width=e.width))
        self.main_canvas.bind("<MouseWheel>",
            lambda e: self.main_canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units"))

        tk.Label(self.content_frame,
                 text="Open a .db file to begin reviewing ads",
                 bg=BG, fg=TEXT_MUTED,
                 font=("Segoe UI", 14)).pack(expand=True, pady=80)

        self.field_widgets = {}

    # ── Record view ───────────────────────────────────────────────────────────
    def _build_record_view(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
        self.field_widgets.clear()

        PX = 20

        # ── Original Message card (always visible, scrollable) ────────────────
        om = tk.Frame(self.content_frame, bg=CARD,
                      highlightbackground=ACCENT, highlightthickness=1)
        om.pack(fill="x", padx=PX, pady=(16, 4))

        tk.Label(om, text="ORIGINAL MESSAGE", bg=CARD, fg=ACCENT2,
                 font=("Segoe UI", 8, "bold"), anchor="w"
                 ).pack(fill="x", padx=12, pady=(10, 2))

        self.original_text = tk.Text(
            om, bg=ENTRY_BG, fg=TEXT_DIM,
            font=("Segoe UI", 10), relief="flat", wrap="word",
            bd=0, height=10, insertbackground=TEXT,
            selectbackground=ACCENT)
        self.original_text.pack(fill="x", padx=12, pady=(0, 10))
        self.original_text.config(state="disabled")

        original_val = self.current.get("original_message") or ""
        self.original_text.config(state="normal")
        self.original_text.insert("1.0", original_val)
        self.original_text.config(state="disabled")

        # ── Meta section (collapsible - contains ad snippet) ──────────────────
        self.meta_outer = tk.Frame(self.content_frame, bg=BG)
        self.meta_outer.pack(fill="x", padx=PX, pady=(8, 0))

        self.meta_btn = tk.Button(
            self.meta_outer,
            text="▼  Show ad snippet",
            bg=BG, fg=TEXT_MUTED, relief="flat", bd=0,
            font=FONT_SMALL, cursor="hand2", command=self._toggle_meta,
            activebackground=BG, activeforeground=TEXT_DIM)
        self.meta_btn.pack(anchor="w")

        self.meta_card = tk.Frame(self.meta_outer, bg=SNIPPET_BG,
                                  highlightbackground=BORDER, highlightthickness=1)

        mk = tk.Frame(self.meta_card, bg=SNIPPET_BG)
        mk.pack(fill="x", padx=12, pady=(10, 2))
        tk.Label(mk, text="AD SNIPPET", bg=SNIPPET_BG, fg=ACCENT2,
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x")

        self.snippet_text = tk.Text(
            self.meta_card, bg=SNIPPET_BG, fg=TEXT,
            font=("Segoe UI", 11), relief="flat", wrap="word",
            bd=0, height=15, insertbackground=TEXT,
            selectbackground=ACCENT)
        self.snippet_text.pack(fill="x", padx=12, pady=(0, 10))

        snippet_val = self.current.get("ad_snippet") or ""
        self.snippet_text.insert("1.0", snippet_val)
        self.snippet_text.edit_modified(False)
        self.snippet_text.bind("<<Modified>>", self._on_snippet_modified)
        self.snippet_text.bind(
            "<Configure>", lambda _e: self._schedule_snippet_autosize())

        # auto-size after layout pass
        self.after(20, self._schedule_snippet_autosize)

        # ── Fields section ────────────────────────────────────────────────────
        self.fields_outer = tk.Frame(self.content_frame, bg=BG)
        self.fields_outer.pack(fill="x", padx=PX, pady=(8, 0))

        self.fields_btn = tk.Button(
            self.fields_outer, text="▼  Show all fields",
            bg=BG, fg=TEXT_MUTED, relief="flat", bd=0,
            font=FONT_SMALL, cursor="hand2", command=self._toggle_fields,
            activebackground=BG, activeforeground=TEXT_DIM)
        self.fields_btn.pack(anchor="w")

        self.fields_card = tk.Frame(self.fields_outer, bg=CARD,
                                    highlightbackground=BORDER,
                                    highlightthickness=1)
        self._build_field_rows(self.fields_card)

        tk.Frame(self.content_frame, bg=BG, height=24).pack()

        if self.meta_visible:
            self.meta_card.pack(fill="x", pady=(4, 0))
            self.meta_btn.config(
                text="▲  Hide ad snippet")
        if self.fields_visible:
            self.fields_card.pack(fill="x", pady=(4, 0))
            self.fields_btn.config(text="▲  Hide fields")

    # ── Snippet auto-size ─────────────────────────────────────────────────────
    def _schedule_snippet_autosize(self, delay=10):
        if self._snippet_resize_job:
            try:
                self.after_cancel(self._snippet_resize_job)
            except Exception:
                pass
        self._snippet_resize_job = self.after(delay, self._autosize_snippet)

    def _on_snippet_modified(self, _event=None):
        if not getattr(self, "snippet_text", None):
            return
        if self.snippet_text.edit_modified():
            self.snippet_text.edit_modified(False)
            self._schedule_snippet_autosize()

    def _autosize_snippet(self):
        try:
            w = self.snippet_text
            w.update_idletasks()
            counts = w.count("1.0", "end-1c", "displaylines")
            display_lines = int(counts[0]) if counts else 1
            w.config(height=max(12, display_lines))

            self.content_frame.update_idletasks()
            self.main_canvas.configure(
                scrollregion=self.main_canvas.bbox("all"))
            self._snippet_resize_job = None
        except Exception:
            pass

    # ── Field rows ────────────────────────────────────────────────────────────
    def _build_field_rows(self, parent):
        for group in FIELD_ORDER:
            row_frame = tk.Frame(parent, bg=CARD)
            row_frame.pack(fill="x", padx=12, pady=4)
            for field in group:
                self._build_single_field(row_frame, field)

    def _build_single_field(self, parent, field):
        cell = tk.Frame(parent, bg=CARD)
        cell.pack(side="left", padx=(0, 8),expand=True)

        tk.Label(cell, text=LABEL_MAP.get(field, field),
                 bg=CARD, fg=TEXT_DIM,
                 font=("Segoe UI", 8), anchor="w").pack(fill="x")

        val = self.current.get(field)

        if field in ENUM_FIELDS:
            var = tk.StringVar(value=str(val) if val else "")
            ttk.Combobox(cell, textvariable=var,
                         values=ENUM_FIELDS[field],
                         state="readonly", font=FONT_SMALL).pack(fill="x")
            self.field_widgets[field] = ("enum", var)

        elif field in BOOL_FIELDS:
            var = tk.BooleanVar(value=bool(val))
            tk.Checkbutton(cell, variable=var, bg=CARD, fg=TEXT,
                           selectcolor=ACCENT, activebackground=CARD,
                           font=FONT_SMALL, text="Yes").pack(anchor="w")
            self.field_widgets[field] = ("bool", var)

        elif field in NUM_FIELDS:
            display_value = (format_price_display(val)
                             if field == "price"
                             else (str(val) if val not in (None, "") else ""))
            var = tk.StringVar(value=display_value)
            tk.Entry(cell, textvariable=var, bg=ENTRY_BG, fg=TEXT,
                     insertbackground=TEXT, relief="flat", font=FONT_SMALL,
                     bd=4, highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=ACCENT).pack(fill="x")
            self.field_widgets[field] = ("num", var)

        else:
            if field == "phone_numbers":
                if isinstance(val, list):
                    display = ", ".join(val)
                elif val:
                    try:
                        display = ", ".join(json.loads(val))
                    except Exception:
                        display = str(val)
                else:
                    display = ""
                var = tk.StringVar(value=display)
            else:
                var = tk.StringVar(
                    value=str(val) if val not in (None, "") else "")
            tk.Entry(cell, textvariable=var, bg=ENTRY_BG, fg=TEXT,
                     insertbackground=TEXT, relief="flat", font=FONT_SMALL,
                     bd=4, highlightthickness=1,
                     highlightbackground=BORDER,
                     highlightcolor=ACCENT).pack(fill="x")
            self.field_widgets[field] = ("str", var)

    def _toggle_meta(self):
        self.meta_visible = not self.meta_visible
        if self.meta_visible:
            self.meta_card.pack(fill="x", pady=(4, 0))
            self.meta_btn.config(
                text="▲  Hide original message")
        else:
            self.meta_card.pack_forget()
            self.meta_btn.config(
                text="▼  Show original message")

    def _toggle_fields(self):
        self.fields_visible = not self.fields_visible
        if self.fields_visible:
            self.fields_card.pack(fill="x", pady=(4, 0))
            self.fields_btn.config(text="▲  Hide fields")
        else:
            self.fields_card.pack_forget()
            self.fields_btn.config(text="▼  Show all fields")

    # ── DB ────────────────────────────────────────────────────────────────────
    def _open_file_dialog(self):
        path = filedialog.askopenfilename(
            title="Open SQLite database",
            filetypes=[("SQLite DB", "*.db *.sqlite *.sqlite3"),
                       ("All", "*.*")])
        if path:
            self._load_db(path)

    def _load_db(self, path):
        try:
            if self.conn:
                self.conn.close()
            self.conn     = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=DELETE")
            self.db_path  = path
            self.verified = load_verified(path)
            self._fetch_records()
            self.title(f"RE·REVIEW — {os.path.basename(path)}")
        except Exception as ex:
            messagebox.showerror("Error", f"Could not open database:\n{ex}")

    def _fetch_records(self):
        cur = self.conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        if not tables:
            messagebox.showerror("Error", "No tables found in database.")
            return
        self.table_name = tables[0]
        cur.execute(
            f"SELECT * FROM {self.table_name}")
        self.records = [dict(r) for r in cur.fetchall()]
        self._update_stats()
        self._full_sidebar_rebuild()
        if self.records:
            self._show_record(0)

    def _update_stats(self):
        done  = sum(1 for r in self.records if r["id"] in self.verified)
        self.stats_var.set(f"{done}/{len(self.records)} verified")

    # ── Sidebar rebuild (full — on load / search / filter change) ────────────
    def _full_sidebar_rebuild(self):
        for w in self.sb_list.winfo_children():
            w.destroy()
        self._sb_items.clear()
        self._active_sb_id = None

        query = self.search_var.get().strip().lower()
        if query.startswith("🔍"):
            query = ""
        filt = self.filter_var.get()

        by_date = defaultdict(list)
        for idx, rec in enumerate(self.records):
            by_date[parse_date(rec.get("ad_date"))].append((idx, rec))

        for d in sorted(by_date.keys(),
                        key=lambda x: x or datetime.min.date()):
            filtered = []
            for idx, rec in by_date[d]:
                is_ver = rec["id"] in self.verified
                if filt == "verified" and not is_ver:
                    continue
                if filt == "pending" and is_ver:
                    continue
                snippet = (rec.get("ad_snippet") or "").lower()
                city    = (rec.get("city") or "").lower()
                if query and query not in snippet and query not in city:
                    continue
                filtered.append((idx, rec))
            if not filtered:
                continue

            hdr = tk.Frame(self.sb_list, bg=PANEL)
            hdr.pack(fill="x")
            tk.Label(hdr, text=fmt_date_header(d),
                     bg=PANEL, fg=ACCENT2,
                     font=("Segoe UI", 8, "bold"),
                     anchor="w", padx=10, pady=5).pack(fill="x")
            tk.Frame(hdr, bg=BORDER, height=1).pack(fill="x")

            for idx, rec in filtered:
                self._build_sidebar_item(idx, rec)

        if self.current:
            self._highlight_sidebar_item(self.current["id"])

    def _build_sidebar_item(self, idx, rec):
        rec_id = rec["id"]
        is_ver = rec_id in self.verified
        bg_col = GREEN_DIM if is_ver else PANEL
        fg_col = GREEN_FG  if is_ver else TEXT_DIM

        outer = tk.Frame(self.sb_list, bg=bg_col, cursor="hand2")
        outer.pack(fill="x")

        indicator = tk.Frame(outer, bg=bg_col, width=3)
        indicator.pack(side="left", fill="y")

        inner = tk.Frame(outer, bg=bg_col)
        inner.pack(fill="x", padx=8, pady=5)

        top = tk.Frame(inner, bg=bg_col)
        top.pack(fill="x")
        tk.Label(top, text=f"#{rec_id}", bg=bg_col, fg=ACCENT2,
                 font=("Segoe UI", 8, "bold")).pack(side="left")
        ptype = rec.get("property_type") or ""
        ttype = rec.get("transaction_type") or ""
        tag   = f"  {ptype} · {ttype}".strip(" ·")
        if tag:
            tk.Label(top, text=tag, bg=bg_col, fg=fg_col,
                     font=("Segoe UI", 8)).pack(side="left", padx=4)
        if is_ver:
            tk.Label(top, text="✓", bg=bg_col, fg=GREEN_FG,
                     font=("Segoe UI", 9, "bold")).pack(side="right")

        tk.Label(inner, text=(rec.get("ad_snippet") or "—")[:70],
                 bg=bg_col, fg=fg_col,
                 font=("Segoe UI", 9), anchor="w",
                 wraplength=210, justify="left").pack(fill="x")

        city  = rec.get("city") or ""
        price = rec.get("price")
        curr  = rec.get("currency") or ""
        try:
            price_str = f"{format_price_display(price)} {curr}".strip() if price else ""
        except Exception:
            price_str = f"{price} {curr}".strip() if price else ""
        hint = "  ".join(filter(None, [city, price_str]))
        if hint:
            tk.Label(inner, text=hint, bg=bg_col, fg=TEXT_MUTED,
                     font=("Segoe UI", 8), anchor="w").pack(fill="x")

        tk.Frame(self.sb_list, bg=BORDER, height=1).pack(fill="x")

        self._sb_items[rec_id] = (outer, inner, indicator, top,
                                  is_ver, bg_col, fg_col)

        cb = lambda e, i=idx: self._show_record(i)
        outer.bind("<Button-1>", cb)
        for w in self._all_children(outer):
            w.bind("<Button-1>", cb)

    @staticmethod
    def _all_children(widget):
        result = []
        for child in widget.winfo_children():
            result.append(child)
            result.extend(App._all_children(child))
        return result

    # ── Sidebar highlight (O(1) — no rebuild) ─────────────────────────────────
    def _highlight_sidebar_item(self, rec_id):
        # remove highlight from previous
        if self._active_sb_id and self._active_sb_id in self._sb_items:
            prev = self._sb_items[self._active_sb_id]
            outer, inner, indicator, top, is_ver, bg, fg = prev
            indicator.config(bg=bg)   # restore indicator colour
            self._recolor_item(outer, inner, top, bg, fg)

        self._active_sb_id = rec_id

        if rec_id not in self._sb_items:
            return
        outer, inner, indicator, top, is_ver, bg, fg = self._sb_items[rec_id]
        indicator.config(bg=ACCENT)
        self._recolor_item(outer, inner, top, bg, fg)
        self.after(20, lambda: self._scroll_sidebar_to(outer))

    def _recolor_item(self, outer, inner, top, bg, fg):
        for w in [outer, inner, top] + self._all_children(inner):
            try:
                if isinstance(w, tk.Label):
                    cur = w.cget("fg")
                    if cur not in (ACCENT2, GREEN_FG, TEXT_MUTED):
                        w.config(bg=bg, fg=fg)
                    else:
                        w.config(bg=bg)
                else:
                    w.config(bg=bg)
            except Exception:
                pass

    def _scroll_sidebar_to(self, widget):
        try:
            self.sb_canvas.update_idletasks()
            item_y   = widget.winfo_y()
            total_h  = self.sb_list.winfo_height()
            canvas_h = self.sb_canvas.winfo_height()
            if total_h > 0:
                frac = max(0.0, item_y / total_h -
                           canvas_h / (2 * total_h))
                self.sb_canvas.yview_moveto(frac)
        except Exception:
            pass

    # ── Navigation ────────────────────────────────────────────────────────────
    def _show_record(self, idx):
        if not self.records:
            return
        idx = max(0, min(idx, len(self.records) - 1))
        self.current_idx = idx
        self.current     = self.records[idx]
        self._build_record_view()
        is_ver = self.current["id"] in self.verified
        self.rec_label.config(
            text=(f"Record {idx+1} of {len(self.records)}"
                  f"  —  ID {self.current['id']}"
                  + ("  ✓" if is_ver else "")),
            fg=GREEN_FG if is_ver else TEXT_DIM)
        self._highlight_sidebar_item(self.current["id"])
        self.main_canvas.yview_moveto(0)

    def _go_prev(self):
        if self.current_idx > 0:
            self._show_record(self.current_idx - 1)

    def _go_next(self):
        if self.current_idx < len(self.records) - 1:
            self._show_record(self.current_idx + 1)

    def _next_unverified(self):
        for i in range(self.current_idx + 1, len(self.records)):
            if self.records[i]["id"] not in self.verified:
                return i
        for i in range(0, self.current_idx):
            if self.records[i]["id"] not in self.verified:
                return i
        return None

    # ── Save ──────────────────────────────────────────────────────────────────
    def _collect_edits(self):
        updates = {}
        updates["ad_snippet"] = self.snippet_text.get("1.0", "end").strip()
        for field, (kind, var) in self.field_widgets.items():
            if kind == "bool":
                updates[field] = 1 if var.get() else 0
            elif kind == "num":
                raw = normalize_price_input(var.get())
                if raw == "":
                    updates[field] = None
                else:
                    try:
                        updates[field] = (float(raw) if "." in raw
                                          else int(raw))
                    except ValueError:
                        updates[field] = raw
            elif field == "phone_numbers":
                parts = [p.strip() for p in var.get().split(",")
                         if p.strip()]
                updates[field] = json.dumps(parts, ensure_ascii=False)
            else:
                updates[field] = var.get().strip() or None
        return updates

    def _save_current(self):
        if not self.current or not self.conn:
            return
        updates = self._collect_edits()
        if not updates:
            return
        cols = ", ".join(f"{k}=?" for k in updates)
        vals = list(updates.values()) + [self.current["id"]]
        try:
            sql = f"UPDATE {self.table_name} SET {cols} WHERE id=?"
            cur = self.conn.cursor()
            cur.execute(sql, vals)
            self.conn.commit()
            self.records[self.current_idx].update(updates)
            self.current = self.records[self.current_idx]
            self._flash_saved()
        except Exception as ex:
            messagebox.showerror("Save error", str(ex))

    def _save_and_next(self):
        self._save_current()
        rec_id = self.current["id"]
        self.verified.add(rec_id)
        save_verified(self.db_path, self.verified)
        self._update_stats()
        self._mark_sidebar_item_verified(rec_id)
        nxt = self._next_unverified()
        if nxt is not None:
            self._show_record(nxt)
        else:
            messagebox.showinfo("All done!",
                                "All records have been verified 🎉")

    def _mark_sidebar_item_verified(self, rec_id):
        if rec_id not in self._sb_items:
            return
        outer, inner, indicator, top, _, _, _ = self._sb_items[rec_id]
        self._sb_items[rec_id] = (outer, inner, indicator, top,
                                  True, GREEN_DIM, GREEN_FG)
        indicator.config(bg=GREEN_DIM)
        self._recolor_item(outer, inner, top, GREEN_DIM, GREEN_FG)
        existing = [w for w in top.winfo_children()
                    if isinstance(w, tk.Label) and w.cget("text") == "✓"]
        if not existing:
            tk.Label(top, text="✓", bg=GREEN_DIM, fg=GREEN_FG,
                     font=("Segoe UI", 9, "bold")).pack(side="right")

    def _flash_saved(self):
        orig = self.rec_label.cget("text")
        self.rec_label.config(text="  ✓ Saved!", fg=GREEN_FG)
        self.after(1200, lambda: self.rec_label.config(
            text=orig,
            fg=GREEN_FG if self.current["id"] in self.verified
            else TEXT_DIM))

    def _on_closing(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        # Remove WAL/SHM files
        if self.db_path:
            for suffix in ["-wal", "-shm"]:
                wal_path = self.db_path + suffix
                try:
                    if os.path.exists(wal_path):
                        os.remove(wal_path)
                except Exception:
                    pass
        self.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()