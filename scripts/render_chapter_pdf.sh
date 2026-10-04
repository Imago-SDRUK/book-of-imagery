#!/usr/bin/env bash
# Render a single book chapter as a standalone PDF.
#
# Book-format PDF/Typst output always merges every chapter listed in
# _quarto.yml's `chapters:` into one document, so rendering just one chapter
# means temporarily taking it out of that list. This script does that,
# renders a throwaway copy of the file with any trailing author-notes
# section stripped (default marker: "To do:", since that kind of note isn't
# meant for the reader), and restores _quarto.yml afterwards no matter how
# the render goes.
#
# Typst-specific quirks handled on the throwaway copy only (source .qmd is
# never touched):
#  - `.column-margin .callout-note` divs don't compile in this Quarto/Typst
#    combo (fails with "unknown variable: note"), so those blocks are
#    dropped for --to typst.
#  - Typst sandboxes file access to a "root" directory. For a standalone
#    (non-book-listed) render that root ends up being the chapter's own
#    directory, so a chapter-relative path like "../references.bib" is
#    rejected as escaping it. The throwaway copy is built at the project
#    root instead, with its image/bibliography paths rewritten to be
#    root-relative, so nothing needs to climb above the root at all.
set -euo pipefail

usage() { echo "Usage: $0 <chapter.qmd> [--to typst|pdf] [--strip-after <marker regex>]" >&2; exit 1; }

file="${1:?$(usage)}"; shift || true
to="typst"
strip_marker='^To do:'

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to) to="$2"; shift 2 ;;
    --strip-after) strip_marker="$2"; shift 2 ;;
    *) usage ;;
  esac
done

[[ -f "$file" ]] || { echo "File not found: $file" >&2; exit 1; }

root_dir="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
quarto_yml="$root_dir/_quarto.yml"
[[ -f "$quarto_yml" ]] || { echo "No _quarto.yml found at project root ($root_dir)" >&2; exit 1; }

abs_dir="$(cd "$(dirname "$file")" && pwd)"
abs_file="$abs_dir/$(basename "$file")"
rel_file="${abs_file#"$root_dir"/}"

dir="$(dirname "$file")"
base="$(basename "$file" .qmd)"
tmp_base=".${base}.pdfbuild"
final_pdf="$dir/${base}.pdf"

# Typst builds from the project root (paths rewritten below); other formats
# build in place next to the source file.
if [[ "$to" == "typst" ]]; then
  tmp_qmd="$root_dir/${tmp_base}.qmd"
  produced="$root_dir/${tmp_base}.pdf"
else
  tmp_qmd="$dir/${tmp_base}.qmd"
  produced="$dir/${tmp_base}.pdf"
fi

cleanup() {
  if [[ -f "$quarto_yml.bak" ]]; then
    mv "$quarto_yml.bak" "$quarto_yml"
  fi
  rm -f "$tmp_qmd" "$root_dir/${tmp_base}."* "$dir/${tmp_base}."*
}
trap cleanup EXIT

cp "$quarto_yml" "$quarto_yml.bak"

esc_rel_file=$(printf '%s\n' "$rel_file" | sed 's/[.[\*^$/]/\\&/g')
sed -i -E "s|^([[:space:]]*)- ${esc_rel_file}[[:space:]]*\$|\1# - ${rel_file}|" "$quarto_yml"

drop_notes_filter() {
  awk '
    BEGIN { skipping = 0; fence_len = 0 }
    {
      if (!skipping) {
        if ($0 ~ /^:{3,}[ \t]*\{[^}]*column-margin[^}]*callout-note[^}]*\}/ ||
            $0 ~ /^:{3,}[ \t]*\{[^}]*callout-note[^}]*column-margin[^}]*\}/) {
          match($0, /^:+/)
          fence_len = RLENGTH
          skipping = 1
          next
        }
        print
      } else {
        if ($0 ~ /^:+[ \t]*$/) {
          match($0, /^:+/)
          if (RLENGTH >= fence_len) skipping = 0
        }
        next
      }
    }
  '
}

rewrite_paths_for_root() {
  ORIG_DIR="$abs_dir" ROOT_DIR="$root_dir" python3 -c '
import os, re, sys

orig_dir = os.environ["ORIG_DIR"]
root_dir = os.environ["ROOT_DIR"]

def rewrite(p):
    if re.match(r"^(https?://|/|data:)", p):
        return p
    abs_p = os.path.normpath(os.path.join(orig_dir, p))
    return os.path.relpath(abs_p, root_dir)

# Image path is the last "(...)" on an image line, right before an optional
# trailing "{...}" attribute block -- matched from the end so captions with
# nested markdown links (e.g. an inline attribution link) do not confuse it.
img_end_re = re.compile(r"\]\(([^()\s]+)\)(\{[^}]*\})?[ \t]*$")
bib_scalar_re = re.compile(r"^(\s*bibliography:\s*)(\S+)\s*$")
bib_list_start_re = re.compile(r"^\s*bibliography:\s*$")
bib_item_re = re.compile(r"^(\s*-\s*)(\S+)\s*$")

in_bib_block = False
for line in sys.stdin:
    m = bib_scalar_re.match(line)
    if m:
        line = f"{m.group(1)}{rewrite(m.group(2))}\n"
    elif bib_list_start_re.match(line):
        in_bib_block = True
    elif in_bib_block:
        m2 = bib_item_re.match(line)
        if m2:
            line = f"{m2.group(1)}{rewrite(m2.group(2))}\n"
        else:
            in_bib_block = False
    if line.lstrip().startswith("!["):
        m3 = img_end_re.search(line)
        if m3:
            new_path = rewrite(m3.group(1))
            line = line[:m3.start()] + "](" + new_path + ")" + (m3.group(2) or "") + line[m3.end():]
    sys.stdout.write(line)
'
}

strip_trailing_notes() {
  awk -v marker="$strip_marker" '$0 ~ marker { exit } { print }' "$file"
}

if [[ "$to" == "typst" ]]; then
  echo "Note: dropping .column-margin .callout-note blocks for Typst output (unsupported in this Quarto/Typst combo)." >&2
  strip_trailing_notes | drop_notes_filter | rewrite_paths_for_root > "$tmp_qmd"
else
  strip_trailing_notes > "$tmp_qmd"
fi

render_opts=()
if [[ "$to" == "typst" ]]; then
  # Book context turns on heading numbering (needed for @sec-... refs to
  # resolve in Typst); a standalone render doesn't, so set it explicitly.
  render_opts+=(-M number-sections=true)

  # Typst uses its own native citation engine (citeproc is off for this
  # format), which only picks up `csl:` from the project config for files
  # that are part of the book's `chapters:` list. For a standalone render
  # it's silently ignored, so pass it through explicitly, read from
  # _quarto.yml so there is one source of truth for the style in use.
  csl_value=$(sed -n -E 's/^csl:[[:space:]]*(.+)$/\1/p' "$quarto_yml" | head -1)
  if [[ -n "$csl_value" ]]; then
    render_opts+=(-M "csl=$csl_value")
  fi
fi

quarto render "$tmp_qmd" --to "$to" "${render_opts[@]}"

if [[ -f "$produced" ]]; then
  mv "$produced" "$final_pdf"
  echo "PDF written to $final_pdf"
else
  echo "Render finished but no PDF found at $produced" >&2
  exit 1
fi
