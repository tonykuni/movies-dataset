#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Price input is adj_close. Volume and turnover deduct day-trade once.

Gross volume stays on the row for display. A missing day-trade figure does
not fall back to the gross number. Institutional net flow is not deducted
again. This does not rewrite the locked engines.

  py -3 VDF_MDL036_PriceVolumePolicy_v0100.py selftest
"""
from __future__ import annotations

import sys

POLICY = "adj_close_ex_daytrade"


def _num(value):
    if value is None or value == "":
        return None
    return float(value)


def _deduct(gross, parts, combined):
    nums = [v for v in parts if v is not None]
    if nums and combined is not None and abs(sum(nums) - combined) > 1e-6:
        return None, "CONFLICT"
    if nums:
        return gross - sum(nums), "SPLIT_ONCE"
    if combined is not None:
        return gross - combined, "COMBINED_ONCE"
    return None, "NO_DAYTRADE"


def apply(row: dict) -> dict:
    volume = _num(row.get("volume"))
    value = _num(row.get("value") if row.get("value") is not None else row.get("turnover"))
    vol_net, vol_how = (None, "NO_GROSS") if volume is None else _deduct(
        volume,
        [_num(row.get("daytrade_cash_volume")), _num(row.get("daytrade_margin_volume"))],
        _num(row.get("daytrade_volume")),
    )
    val_net, val_how = (None, "NO_GROSS") if value is None else _deduct(
        value,
        [_num(row.get("daytrade_cash_value")), _num(row.get("daytrade_margin_value"))],
        _num(row.get("daytrade_value")),
    )
    flags = []
    if vol_how == "CONFLICT" or val_how == "CONFLICT":
        flags.append("DAYTRADE_SPLIT_MISMATCH")
    if vol_net is not None and vol_net < 0 or val_net is not None and val_net < 0:
        flags.append("NEGATIVE_NET")
    if vol_how == "NO_DAYTRADE" or val_how == "NO_DAYTRADE":
        flags.append("DAYTRADE_MISSING")
    price = _num(row.get("adj_close"))
    if price is None:
        flags.append("ADJ_CLOSE_MISSING")
    lamp = "RED" if "DAYTRADE_SPLIT_MISMATCH" in flags else ("YELLOW" if flags else "GREEN")
    return {
        "policy": POLICY,
        "date": row.get("date"),
        "ticker": row.get("ticker") or row.get("code"),
        "price": price,
        "price_field": "adj_close",
        "close_audit": _num(row.get("close")),
        "volume_gross": volume,
        "volume": vol_net,
        "volume_field": "volume_minus_daytrade_once",
        "turnover_gross": value,
        "turnover": val_net,
        "volume_rule": vol_how,
        "turnover_rule": val_how,
        "foreign_net": _num(row.get("foreign_net")),
        "flags": flags,
        "lamp": lamp,
    }


def selftest() -> int:
    row = apply({
        "date": "2026-09-25", "ticker": "2330",
        "close": 100, "adj_close": 80,
        "volume": 1000, "value": 100000,
        "daytrade_cash_volume": 150, "daytrade_margin_volume": 50,
        "daytrade_volume": 200, "daytrade_value": 20000,
        "foreign_net": 9,
    })
    if row["price"] != 80 or row["close_audit"] != 100 or row["volume"] != 800 or row["turnover"] != 80000:
        print("[FAIL] base", row)
        return 1
    if row["foreign_net"] != 9 or row["lamp"] != "GREEN":
        print("[FAIL] flow", row)
        return 1
    combined = apply({"adj_close": 10, "volume": 1000, "turnover": 50, "daytrade_volume": 200, "daytrade_value": 10})
    if combined["volume"] != 800 or combined["turnover"] != 40 or combined["volume_rule"] != "COMBINED_ONCE":
        print("[FAIL] combined", combined)
        return 1
    missing = apply({"close": 100, "volume": 1000, "value": 1000})
    if missing["price"] is not None or missing["volume"] is not None or "ADJ_CLOSE_MISSING" not in missing["flags"]:
        print("[FAIL] missing", missing)
        return 1
    clash = apply({
        "adj_close": 1, "volume": 10, "value": 10,
        "daytrade_volume": 4, "daytrade_cash_volume": 1, "daytrade_margin_volume": 1,
        "daytrade_value": 1,
    })
    if clash["volume"] is not None or clash["lamp"] != "RED":
        print("[FAIL] clash", clash)
        return 1
    print("[OK] %s price=adj_close volume=%s" % (POLICY, row["volume"]))
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "selftest":
        return selftest()
    print("verbs: selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
