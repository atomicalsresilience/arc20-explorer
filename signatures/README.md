# Code Signing Certificate

Windows `.exe` binaries from this project are signed with **Authenticode**
through the [SignPath.io](https://signpath.io) Free Code Signing program
for Open Source projects (powered by Sectigo CA).

## Certificate

- **File:** [`ARC20_Indexer.cer`](ARC20_Indexer.cer)
- **Subject:** CN=ARC20 Indexer
- **Algorithm:** RSA 4096
- **Valid from:** 2026-05-10
- **Valid to:** 2035-01-01
- **Usage:** Code Signing
- **SHA-1 Thumbprint:** `280B9422DA9BE552F401307938BA2E4099DBFC96`

## Verify a binary

### PowerShell (Windows)

    Get-AuthenticodeSignature "arc20-explorer.exe" | Format-List

Expected output:

    Status:                 Valid
    SignerCertificate:      [Subject: CN=ARC20 Indexer]
    TimeStamperCertificate: [Subject: ...SignPath...]

### sigcheck (Sysinternals)

    sigcheck.exe -accepteula arc20-explorer.exe

### Linux (osslsigncode)

    sudo apt install osslsigncode
    osslsigncode verify arc20-explorer.exe

## Reporting

If you find a signed binary that does **NOT** match this certificate
or the published SHA-256 hashes from a release, **do NOT execute it**
and report immediately at:

- GitHub Issues: https://github.com/atomicalsresilience/arc20-explorer/issues

Bitwork Labs
