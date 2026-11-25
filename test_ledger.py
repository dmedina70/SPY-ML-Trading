import unittest
from ledger import Bar, Dividend, Split, simulate

class LedgerTests(unittest.TestCase):
    def test_dividend_receivable_survives_sale(self):
        bars=[Bar('2026-01-02',100,100),Bar('2026-01-05',99,99),Bar('2026-01-06',99,99)]
        r=simulate(bars,{'2026-01-02':10,'2026-01-05':0},[Dividend('2026-01-05','2026-01-06',1)],initial_cash=2000,fee_bps=0)
        self.assertEqual(r[1]['receivable'],10)
        self.assertEqual(r[2]['dividend_cash'],10)
        self.assertAlmostEqual(r[-1]['equity'],2000)
    def test_ex_date_open_purchase_no_entitlement(self):
        b=[Bar('2026-01-02',100,100),Bar('2026-01-05',99,99),Bar('2026-01-06',99,99)]
        r=simulate(b,{'2026-01-05':10},[Dividend('2026-01-05','2026-01-06',1)],initial_cash=2000,fee_bps=0)
        self.assertEqual(r[-1]['dividend_cash'],0)
    def test_split_preserves_equity(self):
        b=[Bar('2026-01-02',100,100),Bar('2026-01-05',50,50)]
        r=simulate(b,{'2026-01-02':10},splits=[Split('2026-01-05',2)],initial_cash=2000,fee_bps=0)
        self.assertEqual(r[-1]['shares'],20)
        self.assertAlmostEqual(r[-1]['equity'],2000)
    def test_short_dividend_liability(self):
        b=[Bar('2026-01-02',100,100),Bar('2026-01-05',99,99),Bar('2026-01-06',99,99)]
        r=simulate(b,{'2026-01-02':-10,'2026-01-05':0},[Dividend('2026-01-05','2026-01-06',1)],initial_cash=2000,fee_bps=0)
        self.assertEqual(r[-1]['dividend_cash'],-10)
        self.assertAlmostEqual(r[-1]['equity'],2000)
    def test_fee_charged(self):
        b=[Bar('2026-01-02',100,100)]
        r=simulate(b,{'2026-01-02':5},initial_cash=2000,fee_bps=10)
        self.assertAlmostEqual(r[-1]['fees'],.5)
        self.assertAlmostEqual(r[-1]['equity'],1999.5)
    def test_bad_dividend(self):
        with self.assertRaises(ValueError):
            simulate([Bar('2026-01-02',100,100)],{},[Dividend('2026-01-02','2026-01-01',1)])
    def test_gross_cap(self):
        b=[Bar('2026-01-02',100,100)]
        r=simulate(b,{'2026-01-02':1000},initial_cash=2000,fee_bps=0)
        self.assertEqual(r[0]['shares'],20)
    def test_no_future_dividend_paid_early(self):
        b=[Bar('2026-01-02',100,100),Bar('2026-01-05',99,99),Bar('2026-01-06',99,99)]
        r=simulate(b,{'2026-01-02':10},[Dividend('2026-01-05','2026-01-06',1)],initial_cash=2000,fee_bps=0)
        self.assertEqual(r[1]['dividend_cash'],0)
        self.assertEqual(r[1]['receivable'],10)

if __name__ == '__main__':
    unittest.main()
