# 出典一覧

試算に使った数値の出典。`tools/unit_economics.py` のコメントで `SOURCED` と
付記した定数はすべてここに対応する。`ASSUMED` と付記したものは出典がない仮定値。

## Shopify 料金・決済手数料

- Basic プラン $29/月(年払い) / $39/月(月払い)
  - https://www.connectbooks.com/blog-posts/shopify-fees-2026
  - https://sherocommerce.com/blogs/insights/shopify-pricing
- Shopify Payments: Basic / オンライン決済 2.9% + $0.30 per transaction
  - https://ecommerce.folio3.com/blog/how-does-shopify-payments-work/
- 他社決済ゲートウェイ利用時の追加課金: Basic 2.0% / Shopify 1.0% / Advanced 0.6%
  - https://demetio.com/en/blog/shopify-pricing-comparison/

> 注意: 上記は米国表記のレート。**日本の Shopify Payments のレートは別建ての可能性があり、
> 未確認**。契約前に管理画面の実レートで `--payment-rate` を差し替える必要がある。

## Meta 広告ベンチマーク (EC)

- EC全業種 CVR 中央値 1.57% (2025) / プラットフォーム全体 1.53% (2026)
- EC blended CPM $16.80 / CPC $0.87
- 全業種 CPM 中央値 $13.48 (2025)
- 業種別 CPA 中央値 $26.80 (E-learning) 〜 $51.86 (Electronics)
- 業種別 CVR: Food & Beverage 2.02% (最高) 〜 Electronics 1.20% (最低)
- 繁忙期は CPC が 30-35%、CPM が 25-66% 上昇
  - https://madgicx.com/blog/meta-ads-benchmarking
  - https://www.fibbler.co/blog/facebook-ads-benchmarks
  - https://27five.com/blog/meta-ads-benchmarks-ecommerce-2026/
  - https://www.digitalapplied.com/blog/facebook-ads-benchmarks-2026-cpc-cpm-ctr-industry

## ドロップシッピングの利益率・配送

- 純利益率 15-25% が健全なベンチマーク / 良好とされる範囲は 10-30%、20%前後が健全
  - https://trueprofit.io/blog/dropshipping-profit-margin
  - https://www.autods.com/blog/dropshipping-tips-strategies/dropshipping-profit-margin/
- AliExpress → 日本の配送日数: 追跡付き標準 7-16営業日 / エコノミー 15-35日 /
  プレミアム 4-8営業日。加えて出荷前処理に 1-7日
  - https://www.xsourcingchina.com/aliexpress-shipping-time-by-country-2026-us-uk-canada-australia-japan/

## 日本の少額輸入貨物課税（現行）

- 課税価格の合計額が1万円以下の輸入貨物は関税・消費税が免除
- 個人輸入の課税価格は「海外小売価格 × 60%」で計算 → 海外小売価格 約16,666円以下が免税
- 課税価格20万円以下は簡易税率
- 酒税・たばこ税は免税対象外
  - https://hunade.com/yunyu-16666
  - https://www.customs.go.jp/tsukan/kanizeiritsu.htm
  - https://wise.com/jp/blog/private-import-tax

## 日本の少額輸入貨物課税（2028年4月1日からの改正）

令和8年度(2026年度)税制改正大綱で決定:

- 通信販売により国外から国内に宛てて発送される資産の譲渡（対価1万円(税抜)以下のもの）が
  **消費税の課税対象**になる
- 個人輸入の課税価格 **0.6掛け特例は廃止**
- 一定規模以上（年50億円超）のプラットフォーム事業者へ納税義務を転換する
  **プラットフォーム課税** を導入
- **適用: 2028年4月1日以後の資産の譲渡等**
  - https://www.zeiken.co.jp/zeikenpress/press/0004pp20260113b/
  - https://www.zeiken.co.jp/zeikenpress/wp-content/uploads/2026/01/p004_20260109_01_01.pdf
  - https://equity.jiji.com/commentaries/2025122000288g

背景（財務省WG）:

- 令和6(2024)年の輸入許可件数 約1.9億件 = コロナ禍前(2019)の約4.1倍
- そのうち課税価格1万円以下の貨物が全体の **約9割**
  - https://www.mof.go.jp/about_mof/councils/syogakuyunyuwg/syogakuyunyuwg_gijihaihu/wg20251017.html

> 注意: **販売者・プラットフォーム・輸入者のうち誰が納税義務者になるかの切り分けは
> 本試算では未確認**。自分がドロップシッピング販売者となる場合の取り扱いは税理士・税関に
> 確認が必要。試算では「取引額に消費税10%相当のコストが乗る」ケースとして
> `--apply-2028-import-tax` で感度を見るだけに留めている。

## 日本の法規制

- 無在庫販売を直接禁止する条文はない。受注した商品を約束の期日までに届けられれば適法
- 特定商取引法: 販売業者名・住所・電話番号・責任者名・販売価格・送料・支払方法・
  返品ポリシーの広告への明示義務。**仕入先への責任転嫁は認められない**
- 景品表示法: 在庫がないのに「在庫あり」「即日発送」と表示するのは違法
- 顧客からの損害賠償請求はサプライヤーではなく**販売者**に向く
  - https://www.shopify.com/jp/blog/is-dropshipping-legal
  - https://ec-lawyer.com/7074/
  - https://stockcrew.co.jp/insights/dropshipping-ec-guide

## 既存の自動化ツール（自作の前に検討すべきもの）

- AutoDS: AliExpress/Amazon/Alibaba からの商品発見・インポート・注文自動処理・追跡番号更新
- DSers: AliExpress 商品の Shopify 同期（Shopify 公式推奨）
- Spocket: AI商品リサーチ + ストアビルダー
- Openship (OSS): 複数ショップ運用、AliExpress/Amazon からのドロップシップ、3PLルーティング、
  GraphQL Admin API プレイグラウンド内蔵
  - https://www.shopify.com/blog/automated-dropshipping?country=us&lang=en
  - https://apps.shopify.com/collections/starter-pack-dropshippers
  - https://dev.to/junaid33/openship-open-source-dropshipping-application-and-more-2j1h

## Shopify Admin API（自動出品に使う）

- `productCreate` ミューテーションで商品を一括作成可能。作成時は **unpublished 状態**なので
  公開は別オペレーションが必要
- バリアント（価格・SKU・バーコード・在庫）は `productVariantsBulkCreate` で追加
  - https://shopify.dev/docs/api/admin-graphql/latest/mutations/productCreate
