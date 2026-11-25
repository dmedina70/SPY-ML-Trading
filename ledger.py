"""Cycle 10: single-asset raw-price daily execution and corporate-action ledger.
Orders are TARGET SHARES at open, provided by a precomputed, timestamp-safe policy.
Dividends accrue before ex-date open; payment credits/debits cash at payment date.
Not a broker simulator: excludes settlement, taxes, financing, fractional restrictions.
"""
from dataclasses import dataclass
from collections import defaultdict
import math

@dataclass(frozen=True)
class Bar:
    date: str
    open: float
    close: float

@dataclass(frozen=True)
class Dividend:
    ex_date: str
    pay_date: str
    amount: float

@dataclass(frozen=True)
class Split:
    date: str
    ratio: float


def simulate(bars, targets, dividends=(), splits=(), initial_cash=100000., fee_bps=5., max_gross=1., target_fn=None):
    if initial_cash <= 0 or fee_bps < 0 or not (0 < max_gross <= 1):
        raise ValueError('invalid configuration')
    dates = [b.date for b in bars]
    if len(dates) != len(set(dates)) or dates != sorted(dates):
        raise ValueError('bars must be unique and chronological')
    div_by_ex = defaultdict(list)
    div_by_pay = defaultdict(list)
    split_by_date = defaultdict(list)
    for d in dividends:
        if d.amount < 0 or d.pay_date < d.ex_date or d.ex_date not in dates or d.pay_date not in dates:
            raise ValueError('invalid dividend')
        div_by_ex[d.ex_date].append(d)
        div_by_pay[d.pay_date].append(d)
    for s in splits:
        if s.ratio <= 0 or s.date not in dates:
            raise ValueError('invalid split')
        split_by_date[s.date].append(s)
    cash = float(initial_cash)
    shares = 0.
    receivables = defaultdict(float)
    out = []
    for b in bars:
        if not (math.isfinite(b.open) and math.isfinite(b.close) and b.open > 0 and b.close > 0):
            raise ValueError('invalid raw price')
        for s in split_by_date[b.date]:
            shares *= s.ratio
        for d in div_by_ex[b.date]:
            receivables[d.pay_date] += shares * d.amount
        dividend_cash = receivables.pop(b.date, 0.)
        cash += dividend_cash
        equity_before = cash + shares * b.open + sum(receivables.values())
        if equity_before <= 0:
            raise ValueError('nonpositive account equity')
        requested = float(target_fn(b, shares, cash, sum(receivables.values()), out[-1] if out else None) if target_fn else targets.get(b.date, shares))
        if not math.isfinite(requested):
            raise ValueError('invalid target')
        max_shares = max_gross * equity_before / b.open
        desired = max(-max_shares, min(max_shares, requested))
        if desired > shares and desired >= 0 and shares >= 0:
            affordable = (cash / (b.open * (1 + fee_bps / 10000))) + shares
            desired = max(0., min(desired, affordable))
        delta = desired - shares
        fees = abs(delta) * b.open * fee_bps / 10000
        cash -= delta * b.open + fees
        shares = desired
        receivable = sum(receivables.values())
        equity = cash + shares * b.close + receivable
        out.append(dict(date=b.date, cash=cash, shares=shares, receivable=receivable,
                        dividend_cash=dividend_cash, fees=fees, turnover=abs(delta)*b.open,
                        equity=equity, gross_exposure=abs(shares*b.close)/equity if equity > 0 else float('inf')))
    return out
