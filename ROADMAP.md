# ARC-20 Explorer · Roadmap

> Progressive scaling — from read-only explorer to full wallet
> companion. Every step builds on the previous.

---

## Current state

**v1.0.0** released May 2026 · Read-only explorer · Linux + Windows (signed)

---

## Short term — Q2-Q3 2026

### v1.0.1 · macOS support + bug fixes
- macOS x86_64 build via GitHub Actions
- Fix any issues reported in v1.0.0
- Native review of translations (if community contributes)

### v1.1.0 · Multi-wallet & history
- Multiple wallet profiles (separate sets of addresses)
- BIP-329 labels for addresses and UTXOs
- Transaction history (last 100 per address)
- Export portfolio to CSV / JSON
- Auto-refresh configurable
- Address book with notes

### v1.2.0 · Advanced read features
- Detection of UTXOs at risk (NFT poisoning prevention)
- Configurable alerts (movements, new UTXOs)
- Portfolio statistics with charts
- SPV verification of node responses
- Import from xpub (watch-only of full wallet)

---

## Medium term — Q4 2026 / Q1 2027

### v2.0.0 · PSBT companion
- PSBT viewer and decoder
- Generate **unsigned** PSBTs for transactions
- Coin control to preserve ARC-20 UTXOs (avoid burns)
- Integration with external wallets (Sparrow, hardware wallets)
- Broadcast via configured node

> ⚠️ The app will **never store private keys**. Users sign PSBTs in
> their existing wallet (Sparrow, Wizz, hardware) and bring them
> back for broadcast.

---

## Long term — 2027+

### v3.x · By community demand
Possible directions if user adoption justifies it:

- **Fork of an existing wallet** (e.g. Wizz) with Bitwork branding
- **Browser extension** companion
- **Mobile-friendly read companion** (NOT replacement of current desktop)

### Out of scope (for now)

- Full custody wallet (private key management) — high security risk,
  better delegated to specialized wallets like Wizz, Sparrow, hardware.
- Browser-only deployment — security model would be weaker.
- Tracking, analytics, telemetry — never.

---

## Feature requests

Open an [issue](https://github.com/atomicalsresilience/arc20-explorer/issues)
with the `enhancement` label.

## Translation contributions

If you're a native speaker of any included language, see
`i18n/<code>.json` and submit a PR. The "Status" column in the README
tracks which languages still need native review.

## Code signing

Windows binaries are Authenticode-signed via SignPath.io free OSS
program (since v1.0.0). For macOS notarization we will evaluate
options when v1.0.1 ships.

---

⚛ Powered by ARC20 Bitwork Labs 
