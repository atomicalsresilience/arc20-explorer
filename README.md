# ARC-20 Explorer

[![Version](https://img.shields.io/badge/version-1.0.0-f59e0b)](https://github.com/atomicalsresilience/arc20-explorer/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey)]()

A standalone, open-source desktop app to explore your **ARC-20 tokens, Realms and Bitcoin UTXOs** on the [Atomicals Protocol](https://atomicals.xyz).

> **No web. No tracking. No middlemen.**
> Direct TCP/TLS connection from your machine to the Atomicals node of your choice.

⚛ Powered by **[Bitwork Labs](https://github.com/atomicalsresilience)** · _First Bitwork PoW deterministic protocol on BTC_

---

## Features

- **Standalone**: a single executable, no installation, no dependencies on the user side.
- **Universal**: connects to **any** Atomicals ElectrumX node (TCP `:50001` or TLS `:50002`).
- **Privacy-first**: your Bitcoin addresses never leave your computer except to the node *you* choose.
- **Multi-language**: 11 languages supported (see [Languages](#languages)).
- **Beautiful UI**: dark mode, modern card layout, animated atom welcome screen.
- **Detailed breakdown**:
  - Realms (NFT-style names)
  - Fungible tokens (FT) consolidated balance + per-UTXO detail
  - Spendable Bitcoin
  - Per-wallet UTXO listing with TXID:VOUT for each token

---

## Quick start

### Linux

```bash
# Download from GitHub Releases (see below for hashes)
wget https://github.com/atomicalsresilience/arc20-explorer/releases/download/v1.0.0/arc20-explorer-v1.0.0-linux-x86_64.tar.gz

# Verify checksum (recommended!)
sha256sum arc20-explorer-v1.0.0-linux-x86_64.tar.gz
# Compare with checksums.txt from the release page

# Extract & run
tar xzf arc20-explorer-v1.0.0-linux-x86_64.tar.gz
cd arc20-explorer-v1.0.0-linux-x86_64
./arc20-explorer
```

### Windows / macOS

Coming in v1.1.0.

### From source

```bash
git clone https://github.com/atomicalsresilience/arc20-explorer.git
cd arc20-explorer
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
python3 arc20_explorer.py
```

---

## Languages

| Code | Language | Status |
|------|----------|--------|
| EN | English | ✓ Native |
| ES | Español | ✓ Native |
| ZH | 中文 (简体) | ⚠ Needs native review |
| KO | 한국어 | ⚠ Needs native review |
| RU | Русский | ⚠ Needs native review |
| JA | 日本語 | ⚠ Needs native review |
| PT | Português (BR) | ⚠ Needs native review |
| VI | Tiếng Việt | ⚠ Needs native review |
| TR | Türkçe | ⚠ Needs native review |
| ID | Bahasa Indonesia | ⚠ Needs native review |
| FR | Français | ⚠ Needs native review |

**🌍 Help us improve translations!** If you're a native speaker, open a PR editing the corresponding `i18n/<code>.json` file.

---

## How it works
┌────────────────────────┐
│  Your machine          │
│  ┌──────────────────┐  │
│  │  ARC-20 Explorer │  │
│  │  (this app)      │  │
│  └────────┬─────────┘  │
└───────────┼────────────┘
│ TCP/TLS direct
▼
┌────────────────────┐
│ Any Atomicals node │
│ :50001 / :50002    │
└────────────────────┘

The app makes a direct TCP/TLS connection to the ElectrumX-Atomicals node you specify. **No intermediate servers, no logging, no third-party JavaScript.**

User data is stored only at:
- Linux: `~/.arc20-explorer/config.json`
- Windows: `%USERPROFILE%\.arc20-explorer\config.json`
- macOS: `~/.arc20-explorer/config.json`

---

## Public Atomicals nodes

You can use **any** Atomicals ElectrumX node. 

Our ARC20 Bitwork Labs node is available at:

Host: arc20bitworklabs.duckdns.org
Port: 50001 (TCP) or 50002 (TLS)


---

## Verification

All releases are published with **three independent checksums** so you can verify integrity:

| Algorithm | Purpose |
|-----------|---------|
| `xxh64`   | Fast verification (non-cryptographic) |
| `sha256`  | Cryptographic verification (standard) |
| `md5`     | Legacy compatibility |

Always check at least the **SHA-256** before running a downloaded binary:

```bash
sha256sum arc20-explorer-v1.0.0-linux-x86_64.tar.gz
```

The hash must match the one published in [`checksums.txt`](https://github.com/atomicalsresilience/arc20-explorer/releases/download/v1.0.0/checksums.txt) on the release page.

---

## Build from source

```bash
# Clone
git clone https://github.com/atomicalsresilience/arc20-explorer.git
cd arc20-explorer

# Build
chmod +x build.sh
./build.sh

# Output:
# - dist/arc20-explorer (executable)
# - dist/arc20-explorer-v1.0.0-linux-x86_64.tar.gz
# - dist/checksums.txt
```

---

## Donate

If you find this useful, consider supporting Bitwork Labs:

bc1puu9akjm00lunuvx4zceve6at3dhtlg6cv84whrz25xpzastrjfzqh54ukv

Donations fund the public ARC-20 Atomicals node infrastructure.

---

## License

[MIT](LICENSE) © 2026 Bitwork Labs

---

⚛ Powered by Bitwork Labs · First Bitwork PoW deterministic protocol on BTC


