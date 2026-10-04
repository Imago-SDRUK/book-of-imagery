#!/usr/bin/env bash
# Word count per ## section vs. the goal written in the heading (e.g. "(500w)", "(1k w)").
set -euo pipefail

file="${1:?Usage: $0 <file.qmd>}"

awk '
function goal_words(line,    s, k) {
    sub(/[ \t]*\{[^}]*\}[ \t]*$/, "", line)
    if (match(line, /\([0-9.]+[ \t]*[kK]?[ \t]*w\)[ \t]*$/)) {
        s = substr(line, RSTART, RLENGTH)
        gsub(/[()w \t]/, "", s)
        k = (s ~ /[kK]$/)
        gsub(/[kK]/, "", s)
        return (s + 0) * (k ? 1000 : 1)
    }
    return -1
}
function truncate(label,    maxlen) {
    maxlen = 40
    if (length(label) > maxlen) return substr(label, 1, maxlen - 3) "..."
    return label
}
function report(    label, diff) {
    label = sec
    sub(/^## /, "", label)
    sub(/[ \t]*\{[^}]*\}[ \t]*$/, "", label)
    sub(/[ \t]*\([0-9.]+[ \t]*[kK]?[ \t]*w\)[ \t]*$/, "", label)
    label = truncate(label)
    total_actual += n
    if (goal >= 0) {
        total_goal += goal
        diff = n - goal
        printf "%-43s %5d / %-5d words (%+d)\n", label, n, goal, diff
    } else {
        printf "%-43s %5d words (no goal)\n", label, n
    }
}
/^## / {
    if (sec != "") report()
    sec = $0
    goal = goal_words(sec)
    n = 0
    next
}
{ n += NF }
END {
    if (sec != "") report()
    print "-------------------------------------------------------------"
    if (total_goal > 0) {
        printf "%-43s %5d / %-5d words (%+d)\n", "TOTAL", total_actual, total_goal, total_actual - total_goal
    } else {
        printf "%-43s %5d words\n", "TOTAL", total_actual
    }
}
' "$file"
