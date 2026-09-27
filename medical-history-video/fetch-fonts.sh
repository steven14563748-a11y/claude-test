#!/usr/bin/env bash
# 下载思源黑体 / 思源宋体（Noto Sans SC / Noto Serif SC，SIL OFL 许可）的 woff2 子集
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p fonts
base=https://cdn.jsdelivr.net/npm/@fontsource
for fam in sans serif; do
  for sub in chinese-simplified latin; do
    for w in 400 700 900; do
      out="fonts/${fam}-${sub}-${w}.woff2"
      [ -s "$out" ] || curl -fsSL -o "$out" "$base/noto-${fam}-sc@5/files/noto-${fam}-sc-${sub}-${w}-normal.woff2"
    done
  done
done
ls -la fonts
