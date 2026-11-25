import unittest
from datetime import date,timedelta
from ledger import Bar
from bridge import Signal,run

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.b=[Bar(str(date(2025,1,1)+timedelta(days=i)),100,100) for i in range(12)]
    def sig(self,i,p=.8): return Signal(self.b[i].date,p,'2024-01-01','2024-06-01','2024-12-01')
    def test_timing(self):
        r=run(self.b,[self.sig(0)],roundtrip_bps=0)
        self.assertEqual([x['shares'] for x in r[:7]],[0,200,200,200,200,200,0])
    def test_overlap(self):
        r=run(self.b,[self.sig(i) for i in range(5)],roundtrip_bps=0)
        self.assertEqual(r[5]['shares'],1000)
        self.assertEqual(r[6]['shares'],800)
    def test_cost(self):
        r=run(self.b,[self.sig(0)])
        self.assertAlmostEqual(r[1]['fees'],10)
        self.assertLess(r[-1]['equity'],100000)
    def test_duplicate(self):
        with self.assertRaises(ValueError): run(self.b,[self.sig(0)]*2)
    def test_future(self):
        with self.assertRaises(ValueError): run(self.b,[Signal(self.b[0].date,.8,'2024-01-01','2024-06-01','2025-01-01')])
    def test_tail(self):
        self.assertEqual(run(self.b,[self.sig(8)])[-1]['shares'],0)
    def test_threshold(self):
        self.assertEqual(run(self.b,[self.sig(0,.5)])[1]['shares'],0)

if __name__ == '__main__':
    unittest.main()
