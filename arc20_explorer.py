#!/usr/bin/env python3
"""
ARC-20 EXPLORER — Bitwork Labs
================================
App standalone moderna para consultar tokens ARC-20
contra cualquier nodo Atomicals.

Sin servidor intermedio. Sin tracking. Datos solo en disco local.

Powered by Bitwork Labs
Donate: bc1puu9akjm00lunuvx4zceve6at3dhtlg6cv84whrz25xpzastrjfzqh54ukv

License: MIT
Version: 1.0.0
"""

import hashlib
import json
import math
import re
import socket
import ssl
import sys
import threading
from collections import defaultdict
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

# ═══════════════════════════════════════════════════════════
# META
# ═══════════════════════════════════════════════════════════
APP_VERSION = "1.0.0"
APP_NAME = "ARC-20 Explorer"
DONATION_ADDR = "bc1puu9akjm00lunuvx4zceve6at3dhtlg6cv84whrz25xpzastrjfzqh54ukv"

CONFIG_DIR = Path.home() / ".arc20-explorer"
CONFIG_DIR.mkdir(exist_ok=True)
CONFIG_FILE = CONFIG_DIR / "config.json"

# Resolver rutas (compatible con PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

I18N_DIR = BASE_DIR / "i18n"

# ═══════════════════════════════════════════════════════════
# COLORES BITWORK
# ═══════════════════════════════════════════════════════════
BG = "#0a0e14"
BG_PANEL = "#0d1117"
BG_CARD = "#161b22"
BG_CARD_HOVER = "#1c2128"
FG = "#e6edf3"
FG_MUTED = "#7d8590"
ACCENT = "#f59e0b"
ACCENT_HOVER = "#fbbf24"
GREEN = "#3fb950"
RED = "#f85149"
BLUE = "#58a6ff"
PURPLE = "#bc8cff"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ═══════════════════════════════════════════════════════════
# I18N
# ═══════════════════════════════════════════════════════════
LANGUAGES = [
    ("en", "English", "EN"),
    ("zh", "中文 (简体)", "ZH"),
    ("es", "Español", "ES"),
    ("ko", "한국어", "KO"),
    ("ru", "Русский", "RU"),
    ("ja", "日本語", "JA"),
    ("pt", "Português (BR)", "PT"),
    ("vi", "Tiếng Việt", "VI"),
    ("tr", "Türkçe", "TR"),
    ("id", "Bahasa Indonesia", "ID"),
    ("fr", "Français", "FR"),
]

_translations = {}
_fallback = {}


def load_translations(lang_code):
    """Carga las traducciones del idioma. Hace fallback a inglés."""
    global _translations, _fallback
    if not _fallback:
        try:
            with open(I18N_DIR / "en.json", "r", encoding="utf-8") as f:
                _fallback = json.load(f)
        except Exception:
            _fallback = {}
    try:
        with open(I18N_DIR / f"{lang_code}.json", "r", encoding="utf-8") as f:
            _translations = json.load(f)
    except Exception:
        _translations = {}


def t(key, **kwargs):
    """Obtiene traducción de clave anidada con dot-notation: 'app.title'."""
    keys = key.split(".")

    def lookup(d, ks):
        for k in ks:
            if isinstance(d, dict) and k in d:
                d = d[k]
            else:
                return None
        return d

    val = lookup(_translations, keys)
    if val is None:
        val = lookup(_fallback, keys)
    if val is None:
        return f"[{key}]"
    if kwargs and isinstance(val, str):
        try:
            val = val.format(**kwargs)
        except Exception:
            pass
    return val


# ═══════════════════════════════════════════════════════════
# BECH32 / SCRIPTHASH
# ═══════════════════════════════════════════════════════════
BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
ADDRESS_PATTERN = re.compile(
    r"^(bc1[a-z0-9]{39,87}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$"
)


def bech32_polymod(values):
    GEN = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ v
        for i in range(5):
            chk ^= GEN[i] if ((b >> i) & 1) else 0
    return chk


def bech32_decode(bech):
    bech = bech.lower()
    if any(ord(x) < 33 or ord(x) > 126 for x in bech):
        return (None, None, None)
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech):
        return (None, None, None)
    hrp = bech[:pos]
    data = []
    for x in bech[pos + 1:]:
        if x not in BECH32_CHARSET:
            return (None, None, None)
        data.append(BECH32_CHARSET.index(x))
    polymod = bech32_polymod(
        [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp] + data
    )
    if polymod == 1:
        return (hrp, data[:-6], "bech32")
    if polymod == 0x2bc830a3:
        return (hrp, data[:-6], "bech32m")
    return (None, None, None)


def convertbits(data, frombits, tobits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    for value in data:
        if value < 0 or (value >> frombits):
            return None
        acc = (acc << frombits) | value
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


def address_to_scripthash(address):
    hrp, data, _ = bech32_decode(address)
    if hrp is None or hrp != "bc":
        raise ValueError("Invalid bech32 address")
    witver = data[0]
    decoded = convertbits(data[1:], 5, 8, False)
    if decoded is None:
        raise ValueError("Decode error")
    op = 0x00 if witver == 0 else 0x50 + witver
    spk = bytes([op, len(decoded)] + decoded)
    sha = hashlib.sha256(spk).digest()
    return sha[::-1].hex()


# ═══════════════════════════════════════════════════════════
# RPC AL NODO
# ═══════════════════════════════════════════════════════════
def rpc_call_raw(host, port, use_ssl, method, params=None, timeout=12):
    payload = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params or []
    }) + "\n"
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.settimeout(timeout)
    if use_ssl:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        sock = ctx.wrap_socket(sock, server_hostname=host)
    try:
        sock.sendall(payload.encode("utf-8"))
        buffer = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buffer += chunk
            if b"\n" in buffer:
                break
        for line in buffer.split(b"\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line.decode("utf-8", errors="replace"))
                if isinstance(data, dict) and "id" in data:
                    return data
            except json.JSONDecodeError:
                continue
        return None
    finally:
        sock.close()


def detect_ssl_for_port(port):
    return port == 50002


def rpc_call(host, port, method, params=None, timeout=12, force_ssl=None):
    use_ssl = force_ssl if force_ssl is not None else detect_ssl_for_port(port)
    return rpc_call_raw(host, port, use_ssl, method, params, timeout)


# ═══════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════
def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {
        "host": "arc20bitworklabs.duckdns.org",
        "port": 50001,
        "addresses": [],
        "language": None,
    }


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# ═══════════════════════════════════════════════════════════
# AUDIT
# ═══════════════════════════════════════════════════════════
_meta_cache = {}


def get_token_metadata(host, port, atomical_id):
    if atomical_id in _meta_cache:
        return _meta_cache[atomical_id]
    metadata = {
        "atomical_id": atomical_id, "ticker": None, "type": "unknown",
        "request_realm": None, "atomical_number": None,
    }
    ft = rpc_call(host, port, "blockchain.atomicals.get_ft_info",
                   [atomical_id])
    if ft and "result" in ft and isinstance(ft["result"], dict):
        inner = ft["result"].get("result", ft["result"])
        if isinstance(inner, dict):
            metadata["type"] = inner.get("type", "FT")
            metadata["ticker"] = (inner.get("$ticker") or
                                   inner.get("ticker") or
                                   inner.get("request_ticker"))
            metadata["atomical_number"] = inner.get("atomical_number")
            if metadata["ticker"]:
                _meta_cache[atomical_id] = metadata
                return metadata
    info = rpc_call(host, port, "blockchain.atomicals.get", [atomical_id])
    if info and "result" in info and isinstance(info["result"], dict):
        inner = info["result"].get("result", info["result"])
        if isinstance(inner, dict):
            metadata["type"] = inner.get("type", "unknown")
            metadata["atomical_number"] = inner.get("atomical_number")
            mint_info = inner.get("mint_info", {})
            if isinstance(mint_info, dict):
                args = mint_info.get("args", {})
                metadata["request_realm"] = args.get("request_realm")
                metadata["ticker"] = (args.get("request_ticker") or
                                       metadata["request_realm"])
    _meta_cache[atomical_id] = metadata
    return metadata


def audit_address(host, port, address):
    if not ADDRESS_PATTERN.match(address):
        return {"address": address, "error": t("addresses.invalid_short"),
                "utxos": []}
    try:
        scripthash = address_to_scripthash(address)
    except Exception as e:
        return {"address": address, "error": str(e), "utxos": []}
    resp = rpc_call(host, port,
                     "blockchain.scripthash.listunspent", [scripthash])
    if not resp or "result" not in resp:
        return {"address": address, "error": t("server.no_response_short"),
                "utxos": []}
    utxos = []
    for u in resp["result"]:
        atomicals = u.get("atomicals", {})
        tokens = []
        for atomical_id, balance in atomicals.items():
            meta = get_token_metadata(host, port, atomical_id)
            tokens.append({
                "atomical_id": atomical_id, "balance": balance,
                "ticker": (meta.get("ticker") or "UNKNOWN"),
                "type": meta.get("type") or "unknown",
                "atomical_number": meta.get("atomical_number"),
                "request_realm": meta.get("request_realm"),
            })
        if any(t.get("request_realm") for t in tokens):
            cat = "REALM"
        elif any(tk["type"].upper() in ("NFT", "REALM", "SUBREALM")
                  for tk in tokens):
            cat = "NFT"
        elif tokens:
            cat = "FT"
        else:
            cat = "BITCOIN"
        utxos.append({
            "txid": u.get("tx_hash") or u.get("txid"),
            "vout": u.get("tx_pos", u.get("vout", 0)),
            "value": u.get("value", 0),
            "category": cat,
            "tokens": tokens,
        })
    return {"address": address, "utxos": utxos}


# ═══════════════════════════════════════════════════════════
# WELCOME LANGUAGE PICKER (modal primer arranque)
# ═══════════════════════════════════════════════════════════
class LanguagePickerModal(ctk.CTkToplevel):
    def __init__(self, parent, on_select):
        super().__init__(parent)
        self.title(APP_NAME)
        self.geometry("520x560")
        self.configure(fg_color=BG)
        self.on_select = on_select
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="ARC-20 Explorer",
                      text_color=ACCENT,
                      font=ctk.CTkFont(size=22, weight="bold")
                      ).pack(pady=(24, 4))
        ctk.CTkLabel(self,
                      text="Welcome / 欢迎 / Bienvenido / 환영",
                      text_color=FG, font=ctk.CTkFont(size=14)
                      ).pack(pady=(0, 4))
        ctk.CTkLabel(self, text="Choose your language",
                      text_color=FG_MUTED,
                      font=ctk.CTkFont(size=11, slant="italic")
                      ).pack(pady=(0, 20))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(padx=24, pady=8, fill="both", expand=True)

        for i, (code, name, _short) in enumerate(LANGUAGES):
            row, col = divmod(i, 2)
            btn = ctk.CTkButton(
                grid, text=name, command=lambda c=code: self._pick(c),
                fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
                text_color=FG, corner_radius=8, height=42, width=210,
                border_width=1, border_color="#30363d",
                font=ctk.CTkFont(size=13)
            )
            btn.grid(row=row, column=col, padx=6, pady=4, sticky="ew")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text="Powered by Bitwork Labs",
                      text_color=FG_MUTED,
                      font=ctk.CTkFont(size=10)
                      ).pack(pady=(16, 16))

    def _pick(self, code):
        self.on_select(code)
        self.destroy()


# ═══════════════════════════════════════════════════════════
# UI PRINCIPAL
# ═══════════════════════════════════════════════════════════
class ExplorerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.configure(fg_color=BG)
        self.geometry("960x900")
        self.minsize(820, 700)

        self.config_data = load_config()
        self._atom_canvas = None
        self._electrons = []
        self._orbits = []
        self._atom_cx = 0
        self._atom_cy = 0

        if not self.config_data.get("language"):
            self.withdraw()
            self.after(100, self._show_language_picker)
        else:
            load_translations(self.config_data["language"])
            self._init_main()

    def _show_language_picker(self):
        def on_pick(code):
            self.config_data["language"] = code
            save_config(self.config_data)
            load_translations(code)
            self.deiconify()
            self._init_main()
        LanguagePickerModal(self, on_pick)

    def _init_main(self):
        self.title(f"{APP_NAME} v{APP_VERSION} · Bitwork Labs")
        self._build_ui()
        self._refresh_address_list()

    def _change_language(self, code):
        self.config_data["language"] = code
        save_config(self.config_data)
        load_translations(code)
        self._atom_canvas = None
        for w in self.winfo_children():
            w.destroy()
        self._build_ui()
        self._refresh_address_list()

    def _card(self, parent, **kw):
        return ctk.CTkFrame(
            parent, corner_radius=12, fg_color=BG_PANEL,
            border_width=1, border_color="#21262d", **kw
        )

    def _h2(self, parent, text):
        return ctk.CTkLabel(
            parent, text=text, text_color=ACCENT,
            font=ctk.CTkFont(size=13, weight="bold")
        )

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG, corner_radius=0
        )
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ─── Header con selector idioma ───────────────────
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 16))
        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_col, text=t("app.title").upper(),
            text_color=ACCENT,
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text=t("app.subtitle", version=APP_VERSION),
            text_color=FG_MUTED,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", pady=(2, 0))

        lang_codes = [name for code, name, _ in LANGUAGES]
        current_lang = self.config_data.get("language", "en")
        current_name = next(
            (name for code, name, _ in LANGUAGES if code == current_lang),
            "English"
        )
        self.lang_dropdown = ctk.CTkOptionMenu(
            header, values=lang_codes,
            command=self._on_lang_change,
            fg_color=BG_CARD, button_color=BG_CARD,
            button_hover_color=BG_CARD_HOVER,
            text_color=FG, dropdown_fg_color=BG_PANEL,
            dropdown_text_color=FG, dropdown_hover_color=BG_CARD_HOVER,
            corner_radius=8, width=160, height=32
        )
        self.lang_dropdown.set(current_name)
        self.lang_dropdown.pack(side="right", padx=(8, 0))

        # ─── Card Servidor ────────────────────────────────
        srv_card = self._card(self.scroll)
        srv_card.pack(fill="x", padx=24, pady=8)
        srv_inner = ctk.CTkFrame(srv_card, fg_color="transparent")
        srv_inner.pack(fill="x", padx=18, pady=14)
        self._h2(srv_inner, t("server.section_title")).pack(
            anchor="w", pady=(0, 10))

        host_row = ctk.CTkFrame(srv_inner, fg_color="transparent")
        host_row.pack(fill="x", pady=4)
        ctk.CTkLabel(host_row, text=t("server.host_label"),
                      text_color=FG_MUTED, width=70, anchor="w"
                      ).pack(side="left")
        self.var_host = ctk.StringVar(value=self.config_data["host"])
        ctk.CTkEntry(host_row, textvariable=self.var_host,
                      fg_color=BG_CARD, border_color="#30363d",
                      corner_radius=8, height=34, text_color=FG
                      ).pack(side="left", fill="x", expand=True, padx=(8, 0))

        port_row = ctk.CTkFrame(srv_inner, fg_color="transparent")
        port_row.pack(fill="x", pady=4)
        ctk.CTkLabel(port_row, text=t("server.port_label"),
                      text_color=FG_MUTED, width=70, anchor="w"
                      ).pack(side="left")
        self.var_port = ctk.StringVar(value=str(self.config_data["port"]))
        ctk.CTkEntry(port_row, textvariable=self.var_port,
                      fg_color=BG_CARD, border_color="#30363d",
                      corner_radius=8, width=100, height=34, text_color=FG
                      ).pack(side="left", padx=(8, 0))
        ctk.CTkLabel(port_row, text=t("server.port_help"),
                      text_color=FG_MUTED, font=ctk.CTkFont(size=10)
                      ).pack(side="left", padx=(12, 0))
        ctk.CTkButton(port_row, text=t("server.btn_verify"),
                       fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
                       text_color=FG, corner_radius=8, height=34,
                       border_width=1, border_color="#30363d",
                       width=110, command=self.check_server
                       ).pack(side="right")

        self.lbl_server_status = ctk.CTkLabel(
            srv_inner, text=t("server.status_unverified"),
            text_color=FG_MUTED, font=ctk.CTkFont(size=11)
        )
        self.lbl_server_status.pack(anchor="w", pady=(8, 0))

        # ─── Card Direcciones ─────────────────────────────
        addr_card = self._card(self.scroll)
        addr_card.pack(fill="x", padx=24, pady=8)
        addr_inner = ctk.CTkFrame(addr_card, fg_color="transparent")
        addr_inner.pack(fill="x", padx=18, pady=14)
        self._h2(addr_inner, t("addresses.section_title")).pack(
            anchor="w", pady=(0, 10))

        input_row = ctk.CTkFrame(addr_inner, fg_color="transparent")
        input_row.pack(fill="x", pady=4)
        self.var_new_addr = ctk.StringVar()
        entry = ctk.CTkEntry(
            input_row, textvariable=self.var_new_addr,
            placeholder_text=t("addresses.input_placeholder"),
            fg_color=BG_CARD, border_color="#30363d",
            corner_radius=8, height=36, text_color=FG
        )
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda e: self.add_address())
        ctk.CTkButton(input_row, text="+ " + t("addresses.btn_add"),
                       fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
                       text_color=FG, corner_radius=8, height=36,
                       border_width=1, border_color="#30363d",
                       width=100, command=self.add_address
                       ).pack(side="right", padx=(8, 0))

        self.addr_list_frame = ctk.CTkFrame(
            addr_inner, fg_color=BG_CARD, corner_radius=8
        )
        self.addr_list_frame.pack(fill="x", pady=(10, 6))

        action_row = ctk.CTkFrame(addr_inner, fg_color="transparent")
        action_row.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(action_row, text=t("addresses.btn_clear_all"),
                       fg_color="transparent", hover_color="#1f1112",
                       text_color=RED, corner_radius=8, height=36,
                       border_width=1, border_color="#481414",
                       width=140, font=ctk.CTkFont(size=11),
                       command=self.clear_addresses
                       ).pack(side="left")
        self.btn_query = ctk.CTkButton(
            action_row, text=t("addresses.btn_query"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER,
            text_color="#000", corner_radius=8, height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.query_portfolio
        )
        self.btn_query.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # ─── Card Resultados ───────────────────────────────
        self.results_card = self._card(self.scroll)
        self.results_card.pack(fill="both", expand=True, padx=24, pady=8)
        self.results_inner = ctk.CTkFrame(
            self.results_card, fg_color="transparent")
        self.results_inner.pack(fill="both", expand=True, padx=18, pady=14)
        self._h2(self.results_inner, t("results.section_title")).pack(
            anchor="w", pady=(0, 10))
        self.results_container = ctk.CTkFrame(
            self.results_inner, fg_color="transparent")
        self.results_container.pack(fill="both", expand=True)
        self._render_welcome()

        # ─── Footer ─────────────────────────────────────────
        footer = ctk.CTkFrame(self.scroll, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(8, 20))
        ctk.CTkLabel(footer, text=t("app.footer_powered"),
                      text_color=FG_MUTED, font=ctk.CTkFont(size=10)
                      ).pack(side="left")
        ctk.CTkLabel(footer,
                      text=f"{t('app.footer_donate')}: {DONATION_ADDR}",
                      text_color=FG_MUTED,
                      font=ctk.CTkFont(size=9, family="monospace")
                      ).pack(side="right")

    def _on_lang_change(self, name):
        for code, n, _ in LANGUAGES:
            if n == name:
                self._change_language(code)
                return

    # ─── Welcome con átomo Electron animado (6 órbitas) ────
    def _render_welcome(self):
        for w in self.results_container.winfo_children():
            w.destroy()
        welcome = ctk.CTkFrame(self.results_container, fg_color="transparent")
        welcome.pack(fill="both", expand=True, pady=10)

        atom_canvas = ctk.CTkCanvas(
            welcome, width=200, height=200,
            bg=BG_PANEL, highlightthickness=0
        )
        atom_canvas.pack()
        self._draw_electron_atom(atom_canvas)

        ctk.CTkLabel(welcome, text=t("welcome.screen_title"),
                      text_color=FG,
                      font=ctk.CTkFont(size=16, weight="bold")
                      ).pack(pady=(8, 4))
        ctk.CTkLabel(welcome, text=t("welcome.screen_intro"),
                      text_color=FG_MUTED,
                      font=ctk.CTkFont(size=11), wraplength=600
                      ).pack()
        ctk.CTkLabel(welcome,
                      text=t("welcome.screen_data_location",
                              path=str(CONFIG_DIR)),
                      text_color=FG_MUTED, font=ctk.CTkFont(size=10)
                      ).pack(pady=(10, 0))
        ctk.CTkLabel(welcome, text=t("welcome.screen_powered"),
                      text_color=BLUE,
                      font=ctk.CTkFont(size=10, slant="italic")
                      ).pack(pady=(8, 0))

    def _draw_electron_atom(self, canvas):
        """Atomo con 6 orbitas elipticas y electrones asincronos."""
        cx, cy = 100, 100
        nucleus_r = 10

        # 6 órbitas: rotación, semiejes, velocidad, fase inicial, colores
        self._orbits = [
            {"rot": 0,    "rx": 75, "ry": 28, "speed": 0.090, "phase": 0.0,
             "color": "#60a5fa", "glow": "#93c5fd"},
            {"rot": 30,   "rx": 75, "ry": 28, "speed": 0.072, "phase": 1.2,
             "color": "#3b82f6", "glow": "#60a5fa"},
            {"rot": 60,   "rx": 75, "ry": 28, "speed": 0.105, "phase": 2.4,
             "color": "#1e40af", "glow": "#3b82f6"},
            {"rot": 90,   "rx": 75, "ry": 28, "speed": 0.060, "phase": 3.6,
             "color": "#60a5fa", "glow": "#93c5fd"},
            {"rot": 120,  "rx": 75, "ry": 28, "speed": 0.085, "phase": 4.8,
             "color": "#3b82f6", "glow": "#60a5fa"},
            {"rot": 150,  "rx": 75, "ry": 28, "speed": 0.115, "phase": 6.0,
             "color": "#2563eb", "glow": "#60a5fa"},
        ]

        # Halo del núcleo
        for r in range(24, nucleus_r, -2):
            alpha = (24 - r) / 14
            color = self._mix_color(BG_PANEL, "#1e40af", alpha * 0.4)
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                fill=color, outline="")

        # 6 órbitas elípticas rotadas
        for orbit in self._orbits:
            self._draw_rotated_ellipse(
                canvas, cx, cy, orbit["rx"], orbit["ry"],
                orbit["rot"], "#1e3a5f"
            )

        # Núcleo
        canvas.create_oval(cx - nucleus_r, cy - nucleus_r,
                            cx + nucleus_r, cy + nucleus_r,
                            fill="#1e40af", outline="#3b82f6", width=2)
        canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                            fill="#60a5fa", outline="")

        # 6 electrones (posición inicial en angulo=phase)
        self._electrons = []
        for orbit in self._orbits:
            x, y = self._electron_pos(cx, cy, orbit, orbit["phase"])
            dot = canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                fill=orbit["color"], outline=orbit["glow"], width=2
            )
            self._electrons.append({
                "id": dot, "angle": orbit["phase"], "orbit": orbit
            })

        self._atom_canvas = canvas
        self._atom_cx = cx
        self._atom_cy = cy
        self._animate_electron()

    def _draw_rotated_ellipse(self, canvas, cx, cy, rx, ry, rot_deg, color):
        """Dibuja elipse rotada usando 60 segmentos."""
        rot = math.radians(rot_deg)
        cos_r = math.cos(rot)
        sin_r = math.sin(rot)
        points = []
        N = 60
        for i in range(N + 1):
            theta = (i / N) * 2 * math.pi
            ex = rx * math.cos(theta)
            ey = ry * math.sin(theta)
            x = cx + ex * cos_r - ey * sin_r
            y = cy + ex * sin_r + ey * cos_r
            points.append(x)
            points.append(y)
        canvas.create_line(*points, fill=color, width=1, smooth=True)

    def _electron_pos(self, cx, cy, orbit, angle):
        """Calcula posición (x, y) del electrón en su órbita rotada."""
        rot = math.radians(orbit["rot"])
        cos_r = math.cos(rot)
        sin_r = math.sin(rot)
        ex = orbit["rx"] * math.cos(angle)
        ey = orbit["ry"] * math.sin(angle)
        x = cx + ex * cos_r - ey * sin_r
        y = cy + ex * sin_r + ey * cos_r
        return x, y

    def _animate_electron(self):
        """Anima los 6 electrones con velocidades asíncronas."""
        if self._atom_canvas is None:
            return
        try:
            for el in self._electrons:
                el["angle"] += el["orbit"]["speed"]
                x, y = self._electron_pos(
                    self._atom_cx, self._atom_cy, el["orbit"], el["angle"]
                )
                self._atom_canvas.coords(el["id"],
                                           x - 5, y - 5, x + 5, y + 5)
            self.after(40, self._animate_electron)
        except Exception:
            self._atom_canvas = None

    def _mix_color(self, c1, c2, ratio):
        def hex_to_rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        r1, g1, b1 = hex_to_rgb(c1)
        r2, g2, b2 = hex_to_rgb(c2)
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ─── Lista direcciones ─────────────────────────────────
    def _refresh_address_list(self):
        for w in self.addr_list_frame.winfo_children():
            w.destroy()
        if not self.config_data["addresses"]:
            ctk.CTkLabel(self.addr_list_frame,
                          text=t("addresses.empty_message"),
                          text_color=FG_MUTED,
                          font=ctk.CTkFont(size=11)
                          ).pack(pady=14)
            return
        for idx, addr in enumerate(self.config_data["addresses"]):
            row = ctk.CTkFrame(self.addr_list_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=4)
            short = addr[:14] + "..." + addr[-10:] if len(addr) > 28 else addr
            ctk.CTkLabel(row, text=short, text_color=FG,
                          font=ctk.CTkFont(family="monospace", size=11)
                          ).pack(side="left")
            ctk.CTkButton(row, text="X", width=28, height=24,
                           fg_color="transparent", hover_color="#1f1112",
                           text_color=RED, corner_radius=6,
                           font=ctk.CTkFont(size=12, weight="bold"),
                           command=lambda i=idx: self.remove_address(i)
                           ).pack(side="right")

    def _save(self):
        self.config_data["host"] = self.var_host.get().strip()
        try:
            self.config_data["port"] = int(self.var_port.get())
        except ValueError:
            self.config_data["port"] = 50001
        save_config(self.config_data)

    def add_address(self):
        addr = self.var_new_addr.get().strip()
        if not addr:
            return
        if not ADDRESS_PATTERN.match(addr):
            messagebox.showerror(t("addresses.invalid_title"),
                                  t("addresses.invalid_message",
                                    address=addr))
            return
        if addr in self.config_data["addresses"]:
            messagebox.showinfo(t("addresses.duplicate_title"),
                                  t("addresses.duplicate_message"))
            return
        self.config_data["addresses"].append(addr)
        self._save()
        self._refresh_address_list()
        self.var_new_addr.set("")

    def remove_address(self, idx):
        if 0 <= idx < len(self.config_data["addresses"]):
            self.config_data["addresses"].pop(idx)
            self._save()
            self._refresh_address_list()

    def clear_addresses(self):
        if not self.config_data["addresses"]:
            return
        if messagebox.askyesno(t("addresses.confirm_clear_title"),
                                t("addresses.confirm_clear_message")):
            self.config_data["addresses"] = []
            self._save()
            self._refresh_address_list()

    def check_server(self):
        self._save()
        self.lbl_server_status.configure(
            text=t("server.status_verifying"), text_color=FG_MUTED)
        self.update()

        def worker():
            host = self.config_data["host"]
            port = self.config_data["port"]
            try:
                resp = rpc_call(host, port,
                                 "blockchain.atomicals.get_global", [],
                                 timeout=8)
                if resp and "result" in resp:
                    res = resp["result"]
                    g = res.get("global", res) if isinstance(res, dict) else {}
                    h = g.get("height", 0)
                    a = g.get("atomical_count", 0)
                    h_fmt = f"{h:,}".replace(",", ".")
                    a_fmt = f"{a:,}".replace(",", ".")
                    proto = "TLS" if detect_ssl_for_port(port) else "TCP"
                    msg = t("server.status_connected",
                              protocol=proto, block=h_fmt,
                              atomicals=a_fmt)
                    self.after(0, lambda: self.lbl_server_status.configure(
                        text=msg, text_color=GREEN))
                    return
            except Exception as e:
                err = str(e)[:60]
                self.after(0, lambda: self.lbl_server_status.configure(
                    text=t("server.status_error", message=err),
                    text_color=RED))
                return
            self.after(0, lambda: self.lbl_server_status.configure(
                text=t("server.status_no_response"), text_color=RED))

        threading.Thread(target=worker, daemon=True).start()

    def query_portfolio(self):
        if not self.config_data["addresses"]:
            messagebox.showwarning(
                t("addresses.warn_no_addresses_title"),
                t("addresses.warn_no_addresses_message"))
            return
        self._save()
        self._atom_canvas = None

        for w in self.results_container.winfo_children():
            w.destroy()
        loading = ctk.CTkFrame(self.results_container, fg_color="transparent")
        loading.pack(fill="x", pady=20)
        ctk.CTkLabel(loading, text=t("results.loading"),
                      text_color=FG, font=ctk.CTkFont(size=14)
                      ).pack()
        self.lbl_loading_detail = ctk.CTkLabel(
            loading, text="", text_color=FG_MUTED,
            font=ctk.CTkFont(size=11)
        )
        self.lbl_loading_detail.pack(pady=(8, 0))
        self.btn_query.configure(state="disabled")
        self.update()

        def worker():
            try:
                _meta_cache.clear()
                reports = []
                host = self.config_data["host"]
                port = self.config_data["port"]
                for i, addr in enumerate(self.config_data["addresses"], 1):
                    short = addr[:16] + "..."
                    self.after(0, lambda s=short, n=i: (
                        self.lbl_loading_detail.configure(
                            text=f"  ({n}) {s}"
                        )
                    ))
                    r = audit_address(host, port, addr)
                    reports.append(r)

                global_tokens = defaultdict(lambda: {
                    "balance": 0, "utxos": 0, "type": "FT", "id": ""
                })
                btc_total = 0
                realms = []
                total_utxos = 0
                for r in reports:
                    if "error" in r:
                        continue
                    for u in r["utxos"]:
                        total_utxos += 1
                        if u["category"] == "BITCOIN":
                            btc_total += u["value"]
                        for tk in u["tokens"]:
                            ticker = (tk.get("ticker") or "UNKNOWN").upper()
                            gt = global_tokens[ticker]
                            gt["balance"] += tk["balance"]
                            gt["utxos"] += 1
                            gt["type"] = tk["type"]
                            gt["id"] = tk["atomical_id"]
                            if tk.get("request_realm"):
                                realms.append({
                                    "name": tk["request_realm"],
                                    "number": tk.get("atomical_number"),
                                    "address": r["address"],
                                    "atomical_id": tk["atomical_id"]
                                })

                self.after(0, lambda: self._render_results(
                    reports, dict(global_tokens), btc_total, realms,
                    total_utxos
                ))
            except Exception as e:
                self.after(0, lambda err=str(e): self._render_error(err))
            finally:
                self.after(0, lambda: self.btn_query.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    def _render_error(self, msg):
        for w in self.results_container.winfo_children():
            w.destroy()
        err_card = ctk.CTkFrame(
            self.results_container, fg_color="#2d0d0d",
            border_color=RED, border_width=1, corner_radius=10
        )
        err_card.pack(fill="x", pady=8)
        ctk.CTkLabel(err_card, text=t("results.error_title"),
                      text_color=RED,
                      font=ctk.CTkFont(size=13, weight="bold")
                      ).pack(anchor="w", padx=14, pady=(10, 4))
        ctk.CTkLabel(err_card, text=msg, text_color=FG,
                      font=ctk.CTkFont(size=11),
                      wraplength=820, justify="left"
                      ).pack(anchor="w", padx=14, pady=(0, 10))

    def _render_results(self, reports, tokens, btc, realms, total_utxos):
        self._atom_canvas = None
        for w in self.results_container.winfo_children():
            w.destroy()

        # Resumen
        summary = ctk.CTkFrame(self.results_container,
                                 fg_color=BG_CARD, corner_radius=10)
        summary.pack(fill="x", pady=(0, 12))
        sumrow = ctk.CTkFrame(summary, fg_color="transparent")
        sumrow.pack(fill="x", padx=14, pady=10)
        for label_key, val in [
            ("results.stat_addresses", len(reports)),
            ("results.stat_utxos", total_utxos),
            ("results.stat_tokens", len(tokens)),
            ("results.stat_realms", len(realms)),
        ]:
            stat = ctk.CTkFrame(sumrow, fg_color="transparent")
            stat.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(stat, text=str(val), text_color=ACCENT,
                          font=ctk.CTkFont(size=22, weight="bold")
                          ).pack()
            ctk.CTkLabel(stat, text=t(label_key).upper(),
                          text_color=FG_MUTED, font=ctk.CTkFont(size=10)
                          ).pack()

        # REALMS
        if realms:
            ctk.CTkLabel(self.results_container,
                          text=t("results.section_realms"),
                          text_color=ACCENT,
                          font=ctk.CTkFont(size=13, weight="bold")
                          ).pack(anchor="w", pady=(8, 6))
            for r in realms:
                rcard = ctk.CTkFrame(
                    self.results_container,
                    fg_color="#3d2817", corner_radius=10,
                    border_width=1, border_color="#5c3d20"
                )
                rcard.pack(fill="x", pady=4)
                inner = ctk.CTkFrame(rcard, fg_color="transparent")
                inner.pack(fill="x", padx=14, pady=10)
                top = ctk.CTkFrame(inner, fg_color="transparent")
                top.pack(fill="x")
                ctk.CTkLabel(top, text=r["name"],
                              text_color=ACCENT,
                              font=ctk.CTkFont(size=18, weight="bold")
                              ).pack(side="left")
                num_fmt = (f"#{r['number']:,}".replace(",", ".")
                            if r['number'] else "?")
                ctk.CTkLabel(top, text=num_fmt, text_color=FG_MUTED,
                              font=ctk.CTkFont(size=12)
                              ).pack(side="right")
                addr_short = (r["address"][:20] + "..." +
                                r["address"][-8:] if len(r["address"]) > 32
                                else r["address"])
                ctk.CTkLabel(inner, text=addr_short,
                              text_color=FG_MUTED,
                              font=ctk.CTkFont(family="monospace", size=10)
                              ).pack(anchor="w", pady=(4, 0))

        # TOKENS
        if tokens:
            ctk.CTkLabel(self.results_container,
                          text=t("results.section_tokens"),
                          text_color=BLUE,
                          font=ctk.CTkFont(size=13, weight="bold")
                          ).pack(anchor="w", pady=(16, 6))
            tcard = ctk.CTkFrame(
                self.results_container,
                fg_color=BG_CARD, corner_radius=10
            )
            tcard.pack(fill="x", pady=4)
            head = ctk.CTkFrame(tcard, fg_color="#1c2128", corner_radius=0)
            head.pack(fill="x")
            for label_key, w_val, anchor_val, padx in [
                ("results.table_ticker", 120, "w", (14, 0)),
                ("results.table_balance", 130, "e", 0),
                ("results.table_utxos", 80, "e", 0),
                ("results.table_type", None, "w", (20, 0)),
            ]:
                ctk.CTkLabel(head, text=t(label_key),
                              text_color=FG_MUTED,
                              font=ctk.CTkFont(size=10, weight="bold"),
                              width=w_val if w_val else 0,
                              anchor=anchor_val
                              ).pack(side="left", padx=padx, pady=8)
            sorted_tokens = sorted(tokens.items(),
                                     key=lambda x: -x[1]["balance"])
            for ticker, info in sorted_tokens:
                row = ctk.CTkFrame(tcard, fg_color="transparent")
                row.pack(fill="x")
                bal_fmt = f"{info['balance']:,}".replace(",", ".")
                ctk.CTkLabel(row, text=ticker, text_color=ACCENT,
                              font=ctk.CTkFont(size=12, weight="bold"),
                              width=120, anchor="w"
                              ).pack(side="left", padx=(14, 0), pady=6)
                ctk.CTkLabel(row, text=bal_fmt, text_color=FG,
                              font=ctk.CTkFont(family="monospace", size=12),
                              width=130, anchor="e"
                              ).pack(side="left", pady=6)
                ctk.CTkLabel(row, text=str(info['utxos']),
                              text_color=FG_MUTED,
                              font=ctk.CTkFont(size=11),
                              width=80, anchor="e"
                              ).pack(side="left", pady=6)
                type_color = (PURPLE if info['type'].upper() in
                                 ("NFT", "REALM", "SUBREALM") else BLUE)
                ctk.CTkLabel(row, text=info['type'].upper(),
                              text_color=type_color,
                              font=ctk.CTkFont(size=10, weight="bold"),
                              anchor="w"
                              ).pack(side="left", padx=(20, 0), pady=6)

        # BITCOIN
        ctk.CTkLabel(self.results_container,
                      text=t("results.section_bitcoin"),
                      text_color=GREEN,
                      font=ctk.CTkFont(size=13, weight="bold")
                      ).pack(anchor="w", pady=(16, 6))
        bcard = ctk.CTkFrame(
            self.results_container, fg_color="#0d2818",
            border_width=1, border_color="#1d4a30",
            corner_radius=10
        )
        bcard.pack(fill="x", pady=4)
        binner = ctk.CTkFrame(bcard, fg_color="transparent")
        binner.pack(fill="x", padx=14, pady=12)
        sats_fmt = f"{btc:,}".replace(",", ".")
        ctk.CTkLabel(binner,
                      text=f"{sats_fmt} {t('results.btc_sats_unit')}",
                      text_color=GREEN,
                      font=ctk.CTkFont(size=20, weight="bold")
                      ).pack(side="left")
        btc_amount = btc / 100_000_000
        ctk.CTkLabel(binner,
                      text=f"~ B {btc_amount:.8f}",
                      text_color=FG_MUTED,
                      font=ctk.CTkFont(size=12)
                      ).pack(side="right")

        # WALLETS
        valid_reports = [r for r in reports if "error" not in r]
        if valid_reports:
            ctk.CTkLabel(self.results_container,
                          text=t("results.section_wallets"),
                          text_color=ACCENT,
                          font=ctk.CTkFont(size=13, weight="bold")
                          ).pack(anchor="w", pady=(16, 6))
            for r in valid_reports:
                wcard = ctk.CTkFrame(
                    self.results_container, fg_color=BG_CARD,
                    corner_radius=10
                )
                wcard.pack(fill="x", pady=4)
                whead = ctk.CTkFrame(wcard, fg_color="#1c2128",
                                       corner_radius=0)
                whead.pack(fill="x")
                addr_short = (r["address"][:18] + "..." +
                                r["address"][-12:] if len(r["address"]) > 36
                                else r["address"])
                ctk.CTkLabel(whead, text=addr_short, text_color=FG,
                              font=ctk.CTkFont(family="monospace", size=11),
                              anchor="w"
                              ).pack(side="left", padx=14, pady=8)

                counts = {"REALM": 0, "NFT": 0, "FT": 0, "BITCOIN": 0}
                for u in r["utxos"]:
                    counts[u["category"]] = counts.get(u["category"], 0) + 1
                count_lbl = []
                if counts["REALM"]:
                    count_lbl.append(f"REALM:{counts['REALM']}")
                if counts["NFT"]:
                    count_lbl.append(f"NFT:{counts['NFT']}")
                if counts["FT"]:
                    count_lbl.append(f"FT:{counts['FT']}")
                if counts["BITCOIN"]:
                    count_lbl.append(f"BTC:{counts['BITCOIN']}")
                ctk.CTkLabel(whead, text="  ·  ".join(count_lbl),
                              text_color=FG_MUTED,
                              font=ctk.CTkFont(size=10)
                              ).pack(side="right", padx=14, pady=8)

                if r["utxos"]:
                    uhead = ctk.CTkFrame(wcard, fg_color="transparent")
                    uhead.pack(fill="x", padx=14, pady=(8, 2))
                    ctk.CTkLabel(uhead, text=t("results.table_txid_vout"),
                                  text_color=FG_MUTED,
                                  font=ctk.CTkFont(size=9, weight="bold"),
                                  width=200, anchor="w"
                                  ).pack(side="left")
                    ctk.CTkLabel(uhead, text=t("results.table_sats"),
                                  text_color=FG_MUTED,
                                  font=ctk.CTkFont(size=9, weight="bold"),
                                  width=80, anchor="e"
                                  ).pack(side="left")
                    ctk.CTkLabel(uhead, text=t("results.table_content"),
                                  text_color=FG_MUTED,
                                  font=ctk.CTkFont(size=9, weight="bold"),
                                  anchor="w"
                                  ).pack(side="left", padx=(12, 0))

                    for u in r["utxos"]:
                        urow = ctk.CTkFrame(wcard, fg_color="transparent")
                        urow.pack(fill="x", padx=14, pady=1)
                        cat_marker = {
                            "REALM": "[R]", "NFT": "[N]",
                            "FT": "[F]", "BITCOIN": "[B]"
                        }
                        txid_short = (u["txid"][:10] + "..." +
                                        u["txid"][-6:]
                                        if u["txid"] else "?")
                        txid_str = (f"{cat_marker.get(u['category'], '[?]')} "
                                     f"{txid_short}:{u['vout']}")
                        cat_color = {
                            "REALM": ACCENT, "NFT": RED,
                            "FT": BLUE, "BITCOIN": GREEN
                        }.get(u["category"], FG_MUTED)
                        ctk.CTkLabel(urow, text=txid_str,
                                      text_color=cat_color,
                                      font=ctk.CTkFont(family="monospace",
                                                         size=10),
                                      width=200, anchor="w"
                                      ).pack(side="left")
                        sats_fmt = f"{u['value']:,}".replace(",", ".")
                        ctk.CTkLabel(urow, text=sats_fmt,
                                      text_color=FG_MUTED,
                                      font=ctk.CTkFont(family="monospace",
                                                         size=10),
                                      width=80, anchor="e"
                                      ).pack(side="left")
                        if u["tokens"]:
                            content_parts = []
                            for tk in u["tokens"]:
                                ticker = tk.get("ticker", "?").upper()
                                bal = f"{tk['balance']:,}".replace(",", ".")
                                if tk.get("request_realm"):
                                    content_parts.append(tk['request_realm'])
                                else:
                                    content_parts.append(f"{ticker} {bal}")
                            content_str = "  ·  ".join(content_parts)
                        else:
                            content_str = "—"
                        ctk.CTkLabel(urow, text=content_str,
                                      text_color=FG,
                                      font=ctk.CTkFont(size=10),
                                      anchor="w"
                                      ).pack(side="left", padx=(12, 0),
                                              fill="x", expand=True)
                    ctk.CTkFrame(wcard, fg_color="transparent",
                                  height=8).pack(fill="x")

        # ERRORES
        errors = [r for r in reports if "error" in r]
        if errors:
            ctk.CTkLabel(self.results_container,
                          text=t("results.section_errors"),
                          text_color=RED,
                          font=ctk.CTkFont(size=13, weight="bold")
                          ).pack(anchor="w", pady=(16, 6))
            for r in errors:
                ctk.CTkLabel(self.results_container,
                              text=f"  · {r['address'][:30]}...: {r['error']}",
                              text_color=RED,
                              font=ctk.CTkFont(size=11)
                              ).pack(anchor="w")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = ExplorerApp()
    app.mainloop()
