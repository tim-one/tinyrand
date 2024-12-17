# Runs muvh faster unfrt pypy.

import sys
sys.path.insert(1, '../src')

import tinyrand

prefix = {
    0: [3598423522, 3485745644, 2977953832, 1345907684, 2486396947,
        2713533522, 2458585290, 1896816786, 3489566947, 3099959312],
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

fint = lambda n: format(n, ",")

def get_period(t):
    START = 123
    t.state = START
    tget = t._get
    p = 0
    target = target_inc = 100_000_000
    while True:
        p += 1
        if p >= target:
            print(fint(p), end="\r")
            target += target_inc
        g = tget()
        assert g
        if g == START:
            break
    return p

def check(version):
    SEED = 42
    t = tinyrand.get(version, seed=SEED)
    assert t.NSTATES == 1 << t.BITS

    print("checking period")
    p = get_period(t)
    print(fint(p))
    expected = {0: T32 - 1}[version]
    assert p == expected, (p, expected)

    t.seed(SEED)
    assert [t.get() for i in range(10)] == prefix[version]

from math import factorial, sqrt
from collections import defaultdict
from time import perf_counter as now

def rankperm(a):
    n = len(a)
    result = 0
    for i in range(n - 1):
        lead = a[i]
        nlt = sum(a[j] < lead for j in range(i + 1, n))
        result += nlt * factorial(n - i - 1)
    return result

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
T32 = 1 << 32

def check_chi2(t, n, rng, try_all_seeds=False):
    f = factorial(n)
    totaltrips = len(rng)
    freq = totaltrips / f
    print(f"{f=:,} {freq=:.2f} {rng=!r:} {totaltrips=:,} {try_all_seeds=:}")

    base = list(range(n))
    d = defaultdict(int)
    ntrips = 0
    limit = limit_inc = 1_000_000
    start_time = now()
    for i in rng:
        ntrips += 1
        if ntrips >= limit:
            pdone = ntrips / totaltrips
            elapsed = now() - start_time
            eta = elapsed / ntrips * (totaltrips - ntrips)
            print(f"{pdone:.1%} done; eta {format_seconds(eta)}",
                  end="           \r")
            limit += limit_inc
        xs = base[:]
        if try_all_seeds:
            t.seed(i)
        t.shuffle(xs)
        #assert sorted(xs) == base
        tot = 0
        for x in xs:
            tot = (tot << 4) + x
        d[tot] += 1
    print("total time", format_seconds(now() - start_time), " " * 40)

    missing = f - len(d)
    assert missing >= 0
    chisq = 0
    if missing > 0:
        print(missing, "missing")
        chisq = missing * freq
    chisq += sum((got - freq)**2 / freq for got in d.values())
    df = f - 1
    sdev = sqrt(2.0 * df) or 1.0
    z = (chisq - df) / sdev
    print(f"{df=:,} {chisq=:.2f} {sdev=:.2f} {z=:+.2f}")
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
            k = check_chi2(t, n, range(factorial(n) * 16))
            del k

def drive2():
    for version in tinyrand.SUPPORTED_VERSIONS:
        print("\nversion", version)
        t = tinyrand.get(version)
        for n in range(2, 12):
            print("\nversion", version, "n", n)
            rng = range(1, T32)
            check_chi2(t, n, rng, True)

if __name__ == "__main__":
    drive()
    #drive2()
