# Runs muvh faster unfrt pypy.

import sys
sys.path.insert(1, '../src')

import tinyrand

prefix = {
    0: [10291, 33686, 18285, 43428, 60511,
        1994, 28201, 62888, 23275, 54622],
    1: [10037299, 10453910, 39995245, 1681828, 58453087,
        47450058, 51408425, 28767656, 33774315, 43177310],
    }

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

units = (('d', 3600.0 * 24),
         ('h', 3600.0),
         ('m', 60.0))

def format_seconds(s):
    result = ""
    for tag, f in units:
        n = int(s / f)
        if n or result:
            result += str(n) + tag
        s -= n * f
    return result + format(s, '.1f') + "s"

def check(version):
    SEED = 42
    t = tinyrand.get(version, seed=SEED)
    assert t.NSTATES == 1 << t.BITS
    first = t._get()
    full = {t._get() for i in range(t.NSTATES - 1)}
    full.add(first)
    assert len(full) == t.NSTATES
    assert t._get() == first

    t.seed(SEED)
    assert [t.get() for i in range(10)] == prefix[version]


from math import factorial
from collections import defaultdict
from time import perf_counter as now

# Generate FREQ * factorial(n) shufflings of list(range(n)), and count
# how many of each are found. The expected number of each is FREQ. The
# actual distribution of counts follows a chi square distribution with
# factorial(n)-1 degrees of freedom. We compute that, and compare it to
# the theoretical range bounded by the 5% and 95% critical values.
#
# It's OK if a few of these generate warnings. A truly random generator
# would be _expected_ to do so about 10% of the time! If it happens,
# try it again for the same value of n using different seeds.
#
# It's especially unconcerning to see a stat on the low side:
#
#     *** WARNING *** suspicious chi square ***
#     less than 5% bound 361206.875 < 361478.8635991877
#
# That's saying that the distribution seen is _more_ uniformly FREQ
# than a truly random generator would deliver. For purposes of breaking
# election ties, that's arguably a good thing.
#
# Note: so long as FREQ is a power of 2, the chi square statistic is
# exactly representable as a binary float,
def check_chi2(t, n, FREQ=16):
    f = factorial(n)
    base = list(range(n))
    d = defaultdict(int)
    totaltrips = FREQ * f
    ntrips = 0
    limit = limit_inc = 1_000_000
    start_time = now()
    for i in range(totaltrips):
        ntrips += 1
        if ntrips >= limit:
            pdone = ntrips / totaltrips
            elapsed = now() - start_time
            eta = elapsed / ntrips * (totaltrips - ntrips)
            print(f"{pdone:.1%} done; eta {format_seconds(eta)}",
                  end="           \r")
            limit += limit_inc
        xs = base[:]
        t.shuffle(xs)
        assert sorted(xs) == base
        tot = 0
        for x in xs:
            tot = tot * 100 + x
        d[tot] += 1
    print("total time", format_seconds(now() - start_time), " " * 40)

    missing = f - len(d)
    assert missing >= 0
    chisq = 0
    if missing > 0:
        print(missing, "missing")
        chisq = missing * FREQ
    chisq += sum((got - FREQ)**2 / FREQ for got in d.values())
    print("df", f - 1, "chisq", chisq)
    if n in n2chi:
        lo, hi = n2chi[n]
        assert lo < hi
        if lo <= chisq <= hi:
            print("in 5%-95% bounds", lo, "<=", chisq, "<=", hi)
        else:
            print()
            print("*** WARNING *** suspicious chi square ***")
            if lo > chisq:
                print("less than 5% bound", chisq, "<", lo)
            else:
                assert hi < chisq
                print("greater than 95% bound", chisq, ">", hi)
    return d

def drive(seed=0):
    assert 666 not in tinyrand.SUPPORTED_VERSIONS
    try:
        t = tinyrand.get(version=666)
    except ValueError:
        pass

    for version in tinyrand.SUPPORTED_VERSIONS:
        print("\nversion", version)
        check(version)
        t = tinyrand.get(version, seed)
        for n in range(1, 12):
            print("\nversion", version, "n", n)
            k = check_chi2(t, n)
            del k

if __name__ == "__main__":
    drive()
