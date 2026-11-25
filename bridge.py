"""Frozen long-only signals to raw-price ledger. No model fitting here."""
from dataclasses import dataclass
from datetime import date
import math
from ledger import simulate

@dataclass(frozen=True)
class Signal:
    date: str
    probability: float
    train_end: str
    calibration_end: str
    policy_end: str


def run(bars, signals, threshold=.60, allocation=.20, roundtrip_bps=10,
        dividends=(), splits=(), initial_cash=100000.):
    bars=list(bars); signals=list(signals); splits=list(splits)
    dates=[b.date for b in bars]; idx={d:i for i,d in enumerate(dates)}
    if dates!=sorted(set(dates)) or not dates: raise ValueError('bad calendar')
    if not (0<=threshold<=1 and 0<allocation<=.2 and roundtrip_bps>=0): raise ValueError('bad policy')
    for d in dates: date.fromisoformat(d)
    seen=set(); entries={}
    for s in signals:
        if s.date in seen or s.date not in idx: raise ValueError('duplicate or unknown signal')
        seen.add(s.date)
        for d in (s.train_end,s.calibration_end,s.policy_end): date.fromisoformat(d)
        if not s.train_end<s.calibration_end<s.policy_end<s.date: raise ValueError('invalid provenance')
        if not 0<=s.probability<=1: raise ValueError('invalid probability')
        i=idx[s.date]
        if s.probability>=threshold and i+6<len(bars): entries[i+1]=i+6
    active=[]
    def target(b, shares, cash, receivable, prior):
        i=idx[b.date]
        active[:]=[end for end in active if end>i]
        if i in entries: active.append(entries[i])
        if not active: return 0.
        ratio=math.prod(s.ratio for s in splits if s.date==b.date)
        return len(active)*allocation*prior['equity']/bars[i-1].close*ratio
    return simulate(bars, {}, dividends, splits, initial_cash, roundtrip_bps/2, target_fn=target)
