# Skill Issues: rule-audit

## 20260703 — compound

**事象**: docs/knowledge/ の扱いが本文内で矛盾している。冒頭の役割分担表は「経験・パターン・アンチパターン集 → knowledge-capture 担当」とするが、Step 2 の昇格候補優先順位 2 は「知らなかった仕様・落とし穴 → docs/knowledge/」を compound の昇格先として挙げ、Step 4 にも docs/knowledge への追記手順がある。「@参照は毎セッション展開」の知見をどちらのスキルで保存するか裁量補完が必要だった
**期待**: 境界の明文化（例: 既存トピックへの短い落とし穴追記は compound、新規トピック・まとまったパターン集・ADR は knowledge-capture）、または分担表と手順の整合

> **解決済み（20260703）**: 境界を「既存トピックへの短い落とし穴追記 = compound / 新規トピック・まとまった集積・ADR・語彙 = knowledge-capture」で確定し、compound（When NOT to use・Step 2 優先順位 2〜4・Step 4）と knowledge-capture（役割分担表）の両本文に相互明記。version 1.1。
