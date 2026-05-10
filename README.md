# ARC-20 Explorer

[![Version](https://img.shields.io/badge/version-1.0.0-f59e0b)](https://github.com/atomicalsresilience/arc20-explorer/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows%20%7C%20macOS-lightgrey)]()
[![Signed](https://img.shields.io/badge/Windows-Authenticode%20signed-brightgreen)](signatures/)

A standalone, open-source desktop app to explore your **ARC-20 tokens, Realms and Bitcoin UTXOs** on the [Atomicals Protocol](https://atomicals.xyz).

> **No web. No tracking. No middlemen.**
> Direct TCP/TLS connection from your machine to the Atomicals node of your choice.

⚛ Powered by **[ARC20 Bitwork Labs](https://github.com/atomicalsresilience)** · _First Bitwork PoW deterministic protocol on BTC_

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
- **Windows .exe is Authenticode-signed** through SignPath.io's free OSS program.

---

## 📥 Quick start

### 🪟 Windows (signed with Authenticode ✓)

Download `arc20-explorer-v1.0.0-windows-x86_64.zip` from [Releases](https://github.com/atomicalsresilience/arc20-explorer/releases/latest).

In PowerShell:

    # Verify SHA-256 (recommended)
    Get-FileHash arc20-explorer-v1.0.0-windows-x86_64.zip -Algorithm SHA256

    # Extract
    Expand-Archive arc20-explorer-v1.0.0-windows-x86_64.zip
    cd arc20-explorer-v1.0.0-windows-x86_64

    # Verify Authenticode signature
    Get-AuthenticodeSignature .\arc20-explorer.exe | Format-List

    # Run
    .\arc20-explorer.exe

> ⚠️ **First-launch note:** Microsoft SmartScreen may show a warning even on signed binaries until reputation is established (normal for new signed projects). Click **More info** → **Run anyway**. Your security comes from the cryptographic signature, not the popup.

### 🐧 Linux

    # Download from GitHub Releases
    wget https://github.com/atomicalsresilience/arc20-explorer/releases/download/v1.0.0/arc20-explorer-v1.0.0-linux-x86_64.tar.gz

    # Verify SHA-256 (recommended)
    sha256sum arc20-explorer-v1.0.0-linux-x86_64.tar.gz
    # Compare with checksums.txt from the release page

    # Extract & run
    tar xzf arc20-explorer-v1.0.0-linux-x86_64.tar.gz
    cd arc20-explorer-v1.0.0-linux-x86_64
    ./arc20-explorer

### 🍎 macOS

Coming in v1.0.1.

### From source (any platform)

    git clone https://github.com/atomicalsresilience/arc20-explorer.git
    cd arc20-explorer
    python3 -m venv --system-site-packages venv
    source venv/bin/activate
    pip install -r requirements.txt
    python3 arc20_explorer.py

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

Other public nodes are listed in the [Atomicals Discord](https://discord.com/invite/atomicals).

---

## ✅ Verification & Signing

| Platform | Signature | How to verify |
|----------|-----------|---------------|
| **Windows** | **Authenticode** ✓ | `Get-AuthenticodeSignature` |
| Linux | SHA-256 hash | `sha256sum` |
| macOS | _coming in v1.0.1_ | — |

Windows `.exe` binaries are digitally signed with an **Authenticode certificate** issued by the [SignPath.io](https://signpath.io) Free OSS Code Signing program (powered by Sectigo CA).

The signing certificate is published in this repo at [`signatures/ARC20_Indexer.cer`](signatures/ARC20_Indexer.cer) for full transparency.

**Verify any release before running:**

PowerShell (Windows):

    Get-FileHash arc20-explorer-v1.0.0-windows-x86_64.zip -Algorithm SHA256
    Get-AuthenticodeSignature arc20-explorer.exe | Format-List

Bash (Linux):

    sha256sum arc20-explorer-v1.0.0-linux-x86_64.tar.gz

Compare with values in `checksums.txt` from the release page.

All releases are published with **3 independent checksums** (xxh64, SHA-256, MD5) so you can verify integrity. The most important is **SHA-256** — it's cryptographically secure.

---

## Build from source

    git clone https://github.com/atomicalsresilience/arc20-explorer.git
    cd arc20-explorer
    chmod +x build.sh
    ./build.sh

Output:
- `dist/arc20-explorer` (executable)
- `dist/arc20-explorer-v1.0.0-linux-x86_64.tar.gz`
- `dist/checksums.txt`

---
## 🗺️ Roadmap

See [ROADMAP.md](ROADMAP.md) for the planned evolution of the project.

**Current direction:** Read-only explorer (v1.x) → PSBT companion (v2.x).

The app will never directly handle private keys. For wallet operations, we will integrate with existing trusted wallets (Sparrow, Wizz, hardware wallets) via PSBT.

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
