# Shopify 海外ドロップシッピング 収益モデル検証

Shopify で海外ドロップシッピングを自動化して収益化する前に、
**「そもそも儲かるのか」を実データで検証する**ためのリポジトリ。

当初の方針は「候補商品一覧から選ぶのは人の作業、それ以外は自動化」。
ただし自動化コードを書く前に、ユニットエコノミクスが成立する条件を特定した。

## 結論（3行）

- **売価 12,800円 未満は構造的に赤字**。Meta広告の実勢CPA（$26.80-$56.86 = 4,020-8,529円）が
  損益分岐CPAを上回るため、原価率をどれだけ絞っても賄えない
- **売価 19,800円 / 原価率20% なら純利益率 23%** で成立する。必要な広告CVRが 0.99% と
  中央値 1.53% を下回るので、平均的な運用でも届く
- **2028年4月1日** から1万円以下の越境通信販売も消費税の課税対象になり、個人輸入の
  0.6掛け特例も廃止される。現行ルールが使えるのは残り約1年半

→ 詳細: [docs/01-unit-economics.md](docs/01-unit-economics.md)

## 使い方

```bash
# 既定シナリオ（売価4,980円 = 赤字ケース）
python3 tools/unit_economics.py

# 成立ケース
python3 tools/unit_economics.py --price 19800 --cogs 4000 --inbound-shipping-jpy 800

# 自分の数字に差し替える
python3 tools/unit_economics.py --usd-jpy 152 --payment-rate 0.0325 \
    --price 15800 --cogs 3200 --refund-rate 0.08

# 2028年の税制改正シナリオ
python3 tools/unit_economics.py --price 19800 --cogs 4000 --apply-2028-import-tax

# JSON出力（他のスクリプトから使う場合）
python3 tools/unit_economics.py --json
```

依存ライブラリなし（Python 3 標準ライブラリのみ）。

## ドキュメント

| ファイル | 内容 |
|---|---|
| [docs/01-unit-economics.md](docs/01-unit-economics.md) | 収益モデルの試算と結論、2028年改正の影響 |
| [docs/02-validation-plan.md](docs/02-validation-plan.md) | 合否条件付きの検証手順（V0-V4）と打ち切り条件 |
| [docs/03-automation-design.md](docs/03-automation-design.md) | 自動化の設計。自作範囲と既存ツールの切り分け |
| [docs/sources.md](docs/sources.md) | 全数値の出典。仮定値と実測値の区別 |

## 数値の扱い方針

`tools/unit_economics.py` の各パラメータには `SOURCED` / `ASSUMED` を付記している。

- **SOURCED**: 出典のあるベンチマーク・制度。[docs/sources.md](docs/sources.md) に URL
- **ASSUMED**: 根拠のない仮定値。**自分の実測値に差し替える前提**

結論は計算から直接導けるものだけを書き、未確認の事項（日本の Shopify Payments 実レート、
2028年改正の納税義務者の切り分けなど）は未確認と明記している。

## 次のアクション

[docs/02-validation-plan.md](docs/02-validation-plan.md) の **V0**（試算の前提を実数値に
差し替え）→ **V1**（需要の存在確認・0円）→ **V2**（実CPAの小予算測定・3-5万円）。

自動化コードは V2/V3 に合格してから書く。未合格で作ると赤字を自動で量産する装置になる。
