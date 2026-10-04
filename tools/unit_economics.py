#!/usr/bin/env python3
"""
海外ドロップシッピング(Shopify / 日本向け)のユニットエコノミクス試算。

数値の扱い:
  SOURCED = 出典のある実測値/ベンチマーク (docs/sources.md 参照)
  ASSUMED = 仮定値。根拠がないので必ず自分の数字に差し替える
出典・仮定の区別はパラメータ定義のコメントに付記してある。

使い方:
  python3 tools/unit_economics.py                       # 既定シナリオ
  python3 tools/unit_economics.py --price 9800 --cogs 2200
  python3 tools/unit_economics.py --json                # 機械可読出力
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict, field

# ---------------------------------------------------------------------------
# ベンチマーク定数 (すべて SOURCED。docs/sources.md に URL)
# ---------------------------------------------------------------------------

# Meta広告 EC横断 中央値 (2025-2026)
META_CPM_USD_BLENDED = 16.80        # SOURCED: EC blended CPM
META_CPC_USD_BLENDED = 0.87         # SOURCED: EC blended CPC
META_CVR_MEDIAN_2025 = 0.0157       # SOURCED: EC全業種 中央値 CVR
META_CVR_MEDIAN_2026 = 0.0153       # SOURCED: プラットフォーム全体 中央値 CVR
META_CPA_USD_LOW = 26.80            # SOURCED: 業種別CPA中央値の下限 (E-learning)
META_CPA_USD_HIGH = 51.86           # SOURCED: 業種別CPA中央値の上限 (Electronics)

# ドロップシッピングの純利益率ベンチマーク
DS_NET_MARGIN_HEALTHY_LOW = 0.15    # SOURCED
DS_NET_MARGIN_HEALTHY_HIGH = 0.25   # SOURCED

# 日本の少額輸入貨物: 現行は課税価格1万円以下が免税、課税価格=海外小売価格×0.6
JP_LOW_VALUE_DUTY_FREE_TAXABLE_JPY = 10_000   # SOURCED
JP_PERSONAL_IMPORT_VALUATION_RATIO = 0.6      # SOURCED
JP_LOW_VALUE_TAX_REFORM_EFFECTIVE = "2028-04-01"  # SOURCED: 令和8年度税制改正大綱
JP_CONSUMPTION_TAX_RATE = 0.10                # SOURCED


@dataclass
class Params:
    # --- 為替 ---
    usd_jpy: float = 150.0          # ASSUMED: 要更新。全USD建て数値に効く

    # --- 商品 ---
    price_jpy: float = 4980.0       # ASSUMED: 検証したい売価
    cogs_jpy: float = 1200.0        # ASSUMED: 仕入値 (AliExpress/CJ の商品代)
    inbound_shipping_jpy: float = 300.0  # ASSUMED: 仕入先→顧客の送料
    customer_shipping_revenue_jpy: float = 0.0  # ASSUMED: 顧客から取る送料 (0=送料無料)

    # --- Shopify / 決済 ---
    shopify_monthly_usd: float = 29.0   # SOURCED: Basic 年払い ($39 月払い)
    payment_rate: float = 0.029         # SOURCED: Shopify Payments Basic (US表記)。日本のレートは要確認
    payment_fixed_usd: float = 0.30     # SOURCED: 同上
    third_party_gateway_rate: float = 0.0  # SOURCED: 他社決済を使う場合 Basic=0.020

    # --- 広告 ---
    cpc_usd: float = META_CPC_USD_BLENDED  # SOURCED
    ad_cvr: float = META_CVR_MEDIAN_2026   # SOURCED: 広告クリック→購入

    # --- オペレーション ---
    refund_rate: float = 0.05       # ASSUMED: 返品・不着・チャージバック率
    other_fixed_monthly_jpy: float = 3000.0  # ASSUMED: ドメイン/アプリ/ツール等

    # --- 税 ---
    charge_sales_consumption_tax: bool = False
    # ASSUMED/要確認: 課税事業者なら売上に対し消費税の納税義務が生じる。
    # 開業当初に免税事業者となるかはインボイス登録等で変わるため税理士に確認が必要。
    apply_2028_import_tax: bool = False
    # SOURCED: 2028-04-01 以降、1万円以下の越境通信販売も消費税の課税対象
    # ただし納税義務者(国外事業者/プラットフォーム/販売者)の切り分けは要確認


def usd(p: Params, x: float) -> float:
    return x * p.usd_jpy


def per_order(p: Params) -> dict:
    """1件あたりの損益を広告費を除いて積む(= 広告に使える上限を出す)。"""
    revenue = p.price_jpy + p.customer_shipping_revenue_jpy
    product_cost = p.cogs_jpy + p.inbound_shipping_jpy

    payment_fee = revenue * (p.payment_rate + p.third_party_gateway_rate) \
        + usd(p, p.payment_fixed_usd)

    # 輸入消費税
    taxable_value = p.cogs_jpy * JP_PERSONAL_IMPORT_VALUATION_RATIO
    duty_free_now = taxable_value <= JP_LOW_VALUE_DUTY_FREE_TAXABLE_JPY
    if p.apply_2028_import_tax:
        # 0.6掛け特例廃止 + 1万円以下も課税 → 取引額ベースで消費税
        import_tax = revenue * JP_CONSUMPTION_TAX_RATE
    else:
        import_tax = 0.0 if duty_free_now else taxable_value * JP_CONSUMPTION_TAX_RATE

    # 売上消費税(課税事業者の場合)。簡便に売上の10/110を納税額として置く
    sales_tax = revenue * (JP_CONSUMPTION_TAX_RATE / (1 + JP_CONSUMPTION_TAX_RATE)) \
        if p.charge_sales_consumption_tax else 0.0

    # 返品・不着の期待損失: 原価と決済手数料は戻らない前提
    refund_loss = p.refund_rate * (revenue + product_cost)

    contribution = revenue - product_cost - payment_fee - import_tax - sales_tax - refund_loss

    return {
        "revenue": revenue,
        "product_cost": product_cost,
        "payment_fee": payment_fee,
        "import_tax": import_tax,
        "import_duty_free_under_current_rule": duty_free_now,
        "sales_consumption_tax": sales_tax,
        "refund_loss": refund_loss,
        "contribution_before_ads": contribution,
        "breakeven_cpa_jpy": contribution,
        "breakeven_cpa_usd": contribution / p.usd_jpy,
    }


def ad_economics(p: Params, breakeven_cpa_jpy: float) -> dict:
    """広告ベンチマークと損益分岐CPAを突き合わせる。"""
    cpa_derived_usd = p.cpc_usd / p.ad_cvr          # CPC / CVR から導出
    cpa_derived_jpy = usd(p, cpa_derived_usd)
    required_cvr = p.cpc_usd / (breakeven_cpa_jpy / p.usd_jpy) \
        if breakeven_cpa_jpy > 0 else float("inf")
    return {
        "cpa_derived_from_cpc_cvr_usd": cpa_derived_usd,
        "cpa_derived_from_cpc_cvr_jpy": cpa_derived_jpy,
        "cpa_reported_range_usd": [META_CPA_USD_LOW, META_CPA_USD_HIGH],
        "cpa_reported_range_jpy": [usd(p, META_CPA_USD_LOW), usd(p, META_CPA_USD_HIGH)],
        "profit_per_order_at_derived_cpa": breakeven_cpa_jpy - cpa_derived_jpy,
        "profit_per_order_at_best_reported_cpa": breakeven_cpa_jpy - usd(p, META_CPA_USD_LOW),
        "required_ad_cvr_to_break_even": required_cvr,
        "required_cvr_vs_median_multiple": required_cvr / p.ad_cvr
            if breakeven_cpa_jpy > 0 else float("inf"),
    }


def monthly(p: Params, orders: int, cpa_jpy: float) -> dict:
    u = per_order(p)
    fixed = usd(p, p.shopify_monthly_usd) + p.other_fixed_monthly_jpy
    gross = u["contribution_before_ads"] * orders
    ad_spend = cpa_jpy * orders
    net = gross - ad_spend - fixed
    revenue = u["revenue"] * orders
    return {
        "orders": orders,
        "revenue": revenue,
        "contribution": gross,
        "ad_spend": ad_spend,
        "fixed_cost": fixed,
        "net_profit": net,
        "net_margin": net / revenue if revenue else 0.0,
    }


def required_price(p: Params, cpa_jpy: float, target_margin: float,
                   cogs_ratio: float) -> float:
    """CPAを所与として、目標純利益率を満たす売価を二分探索で求める。
    cogs_ratio: 売価に対する仕入値(商品代)の比率を固定して探索する。"""
    lo, hi = 100.0, 500_000.0
    for _ in range(200):
        mid = (lo + hi) / 2
        q = Params(**{**asdict(p), "price_jpy": mid, "cogs_jpy": mid * cogs_ratio})
        u = per_order(q)
        margin = (u["contribution_before_ads"] - cpa_jpy) / u["revenue"]
        if margin < target_margin:
            lo = mid
        else:
            hi = mid
    return hi


def fmt(x: float) -> str:
    return f"{x:>12,.0f}"


def report(p: Params) -> None:
    u = per_order(p)
    a = ad_economics(p, u["breakeven_cpa_jpy"])

    print("=" * 74)
    print(" 海外ドロップシッピング ユニットエコノミクス")
    print(f" 為替 {p.usd_jpy:.1f} 円/USD (ASSUMED・要更新)")
    print("=" * 74)

    print("\n[1] 1注文あたりの損益 (広告費を除く)")
    print(f"  売上                      {fmt(u['revenue'])} 円")
    print(f"  - 商品原価+送料           {fmt(-u['product_cost'])} 円")
    print(f"  - 決済手数料              {fmt(-u['payment_fee'])} 円"
          f"  ({p.payment_rate*100:.2f}% + ${p.payment_fixed_usd})")
    print(f"  - 輸入消費税              {fmt(-u['import_tax'])} 円"
          f"  (現行免税: {u['import_duty_free_under_current_rule']})")
    print(f"  - 売上消費税              {fmt(-u['sales_consumption_tax'])} 円")
    print(f"  - 返品/不着 期待損 ({p.refund_rate*100:.0f}%) {fmt(-u['refund_loss'])} 円")
    print(f"  {'-'*56}")
    print(f"  = 広告前 貢献利益         {fmt(u['contribution_before_ads'])} 円"
          f"   (売上比 {u['contribution_before_ads']/u['revenue']*100:.1f}%)")

    print("\n[2] 損益分岐CPA = 広告費に使える上限")
    print(f"  損益分岐CPA               {fmt(u['breakeven_cpa_jpy'])} 円"
          f"  (= ${u['breakeven_cpa_usd']:.2f})")

    print("\n[3] 実勢CPAとの突き合わせ (SOURCED ベンチマーク)")
    print(f"  CPC ${p.cpc_usd} / CVR {p.ad_cvr*100:.2f}% から導出したCPA"
          f"  ${a['cpa_derived_from_cpc_cvr_usd']:.2f}"
          f" = {a['cpa_derived_from_cpc_cvr_jpy']:,.0f} 円")
    print(f"  業種別CPA中央値レンジ      ${META_CPA_USD_LOW:.2f}-${META_CPA_USD_HIGH:.2f}"
          f" = {a['cpa_reported_range_jpy'][0]:,.0f}-{a['cpa_reported_range_jpy'][1]:,.0f} 円")
    print(f"  → 導出CPAでの1件利益      {fmt(a['profit_per_order_at_derived_cpa'])} 円")
    print(f"  → 最良CPAでの1件利益      {fmt(a['profit_per_order_at_best_reported_cpa'])} 円")
    if a["required_ad_cvr_to_break_even"] != float("inf"):
        print(f"  損益分岐に必要な広告CVR    {a['required_ad_cvr_to_break_even']*100:>11.2f}%"
              f"  (中央値の {a['required_cvr_vs_median_multiple']:.1f} 倍)")

    print("\n[4] 月次P&L (導出CPAを使用)")
    cpa = a["cpa_derived_from_cpc_cvr_jpy"]
    print(f"  {'注文数':>6} {'売上':>12} {'貢献利益':>12} {'広告費':>12} "
          f"{'固定費':>10} {'純利益':>12} {'純利益率':>9}")
    for n in (30, 100, 300, 1000):
        m = monthly(p, n, cpa)
        print(f"  {m['orders']:>6} {m['revenue']:>12,.0f} {m['contribution']:>12,.0f} "
              f"{m['ad_spend']:>12,.0f} {m['fixed_cost']:>10,.0f} "
              f"{m['net_profit']:>12,.0f} {m['net_margin']*100:>8.1f}%")

    print("\n[5] 感度分析: 損益分岐CPA (円) / 売価 x 原価率")
    prices = [2980, 4980, 7980, 12800, 19800, 29800]
    ratios = [0.15, 0.20, 0.25, 0.30, 0.40]
    print(f"  {'売価':>8} " + " ".join(f"{'原価'+str(int(r*100))+'%':>10}" for r in ratios))
    for pr in prices:
        row = []
        for r in ratios:
            q = Params(**{**asdict(p), "price_jpy": pr, "cogs_jpy": pr * r,
                          "inbound_shipping_jpy": p.inbound_shipping_jpy})
            row.append(per_order(q)["breakeven_cpa_jpy"])
        print(f"  {pr:>8,} " + " ".join(f"{v:>10,.0f}" for v in row))
    print(f"  ※ 導出CPA {cpa:,.0f} 円 を上回るセルだけが黒字になりうる")

    print("\n[6] 目標純利益率を満たす必要売価 (原価率20%固定)")
    for target in (DS_NET_MARGIN_HEALTHY_LOW, 0.20, DS_NET_MARGIN_HEALTHY_HIGH):
        for label, c in (("導出CPA", cpa),
                         ("最良CPA", usd(p, META_CPA_USD_LOW))):
            rp = required_price(p, c, target, 0.20)
            print(f"  純利益率 {target*100:>4.0f}% / {label} {c:>8,.0f}円"
                  f" → 必要売価 {rp:>10,.0f} 円")

    print("\n[7] 2028-04-01 の税制改正シナリオ")
    print(f"  (SOURCED: 1万円以下の越境通信販売も消費税の課税対象 / 0.6掛け特例廃止)")
    q = Params(**{**asdict(p), "apply_2028_import_tax": True})
    v = per_order(q)
    delta = v["contribution_before_ads"] - u["contribution_before_ads"]
    print(f"  改正前 貢献利益           {fmt(u['contribution_before_ads'])} 円")
    print(f"  改正後 貢献利益           {fmt(v['contribution_before_ads'])} 円")
    print(f"  差分                      {fmt(delta)} 円"
          f"  ({delta/u['contribution_before_ads']*100:+.1f}%)")
    print("=" * 74)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    d = Params()
    for name, val in asdict(d).items():
        if isinstance(val, bool):
            ap.add_argument(f"--{name.replace('_', '-')}", action="store_true",
                            default=val)
        else:
            ap.add_argument(f"--{name.replace('_', '-')}", type=float, default=val)
    ap.add_argument("--price", type=float, help="--price-jpy の別名")
    ap.add_argument("--cogs", type=float, help="--cogs-jpy の別名")
    ap.add_argument("--json", action="store_true", help="JSONで出力")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    kw = {k: v for k, v in vars(args).items()
          if k in Params.__dataclass_fields__}
    if args.price is not None:
        kw["price_jpy"] = args.price
    if args.cogs is not None:
        kw["cogs_jpy"] = args.cogs
    p = Params(**kw)
    if args.json:
        u = per_order(p)
        print(json.dumps({
            "params": asdict(p),
            "per_order": u,
            "ads": ad_economics(p, u["breakeven_cpa_jpy"]),
            "monthly_at_derived_cpa": {
                str(n): monthly(p, n, ad_economics(p, u["breakeven_cpa_jpy"])
                                ["cpa_derived_from_cpc_cvr_jpy"])
                for n in (30, 100, 300, 1000)},
        }, ensure_ascii=False, indent=2))
    else:
        report(p)


if __name__ == "__main__":
    main()
