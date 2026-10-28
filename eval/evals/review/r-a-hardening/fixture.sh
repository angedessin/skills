#!/bin/bash
set -euo pipefail
git -C /Users/kentaro/Desktop/_lab/ai/skills archive 1ff1701 | tar -x
git init -q
git add -A >/dev/null
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "before"
# after の状態に置き換える（追跡中のファイルを消してから展開し、削除も差分に出す）。未コミットのまま残す
git ls-files -z | xargs -0 rm -f
git -C /Users/kentaro/Desktop/_lab/ai/skills archive 309b950 | tar -x
