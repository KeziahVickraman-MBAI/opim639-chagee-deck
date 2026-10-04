#!/bin/sh
# Export the deck to PDF with headless Chrome: one 1280 x 720 page per slide.
#   sh deck/export_pdf.sh
# Writes deck/chagee_deck.pdf (slides) and deck/chagee_deck_notes.pdf (each slide followed by its notes).
set -e
cd "$(dirname "$0")"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
python3 build_deck.py
URL="file://$PWD/chagee_deck.html"
for spec in "chagee_deck.pdf|" "chagee_deck_notes.pdf|?notes=1"; do
  out="${spec%%|*}"; query="${spec#*|}"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=6000 \
    --print-to-pdf="$PWD/$out" "$URL$query" 2>/dev/null
  echo "wrote deck/$out"
done
