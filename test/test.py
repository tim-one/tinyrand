import sys
sys.path.insert(1, '../src')
from tinyrand import TinyRand, MASK

t = TinyRand()
full = {t._get() for i in range(MASK + 1)}
assert len(full) == MASK + 1
del full

t = TinyRand(42)
assert [t.get() for i in range(10)] == \
    [22742, 63965, 15436, 29681, 46670, 63352, 3655, 8742, 3462, 50359]

# .05 and .95 chi square bounds
# https://stattrek.com/online-calculator/chi-square
n2chi = {
    2: (0.003932140000019513, 3.841458820694126),
    3: (1.145476226061769, 11.07049769351635),
    4: (13.0905141881728, 35.17246162690805),
    5: (94.81123693930809, 145.4607402247648),
    6: (657.7831052213778, 782.4906103069768),
    7: (4875.01921297534, 5205.254796153615),
    8: (39853.05348831241, 40787.22056352711),
    9: (361478.8635991877, 364281.4104580742),
    10: (3624368.913253256, 3633231.360808264),
    11: (39902104.0, 39931496.0),
    }

def check(n, seed=0, FREQ=16):
    from math import factorial
    from collections import defaultdict

    t = TinyRand(seed)
    f = factorial(n)
    base = list(range(n))
    d = defaultdict(int)
    for i in range(FREQ * f):
        xs = base[:]
        t.shuffle(xs)
        tot = 0
        for x in xs:
            tot = tot * 100 + x
        d[tot] += 1
    missing = f - len(d)
    assert missing >= 0
    chisq = 0
    if missing > 0:
        print(missing, "missing")
        chisq = missing * FREQ
    chisq += sum((got - FREQ)**2 / FREQ for got in d.values())
    print(n, "df", f - 1, "chisq", chisq)
    if n in n2chi:
        lo, hi = n2chi[n]
        assert lo < hi
        if lo <= chisq <= hi:
            print("in 5%-95% bounds", lo, "<=", chisq, "<=", hi)
        elif lo > chisq:
            print("less than 5% bound", chisq, "<", lo)
        else:
            assert hi < chisq
            print("greater than 95% bound", chisq, ">", hi)
    return d

if 1:
    for n in range(1, 12):
        print("\nn =", n)
        k = check(n)
        del k
