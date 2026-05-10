#!/bin/bash
# Genera checksums xxhash + SHA-256 + MD5 para los .tar.gz en dist/

cd "$(dirname "$0")/dist" 2>/dev/null || exit 1

OUTFILE="checksums.txt"
> "$OUTFILE"

echo "ARC-20 Explorer · Bitwork Labs · Verification checksums" >> "$OUTFILE"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUTFILE"
echo "" >> "$OUTFILE"

if ! command -v xxhsum >/dev/null 2>&1; then
    echo "Instalando xxhash..."
    sudo apt install -y xxhash
fi

for FILE in *.tar.gz; do
    [ -f "$FILE" ] || continue
    echo "── $FILE" >> "$OUTFILE"

    if command -v xxhsum >/dev/null 2>&1; then
        XX=$(xxhsum -H64 "$FILE" 2>/dev/null | awk '{print $1}')
        echo "  xxh64:  $XX" >> "$OUTFILE"
    fi

    SHA=$(sha256sum "$FILE" | cut -d' ' -f1)
    echo "  sha256: $SHA" >> "$OUTFILE"

    MD=$(md5sum "$FILE" | cut -d' ' -f1)
    echo "  md5:    $MD" >> "$OUTFILE"

    SIZE=$(stat -c%s "$FILE")
    echo "  bytes:  $SIZE" >> "$OUTFILE"
    echo "" >> "$OUTFILE"
done

echo "✓ Checksums generados en dist/$OUTFILE"
echo ""
cat "$OUTFILE"
