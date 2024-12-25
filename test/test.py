# Runs muvh faster unfrt pypy.

import sys
sys.path.insert(1, '../src')

import tinyrand
import array, itertools

T32 = 1 << 32
MASK32 = T32 - 1

prefix = {
    0: [2975584321, 1915941066, 2870739003, 2578514367, 4127658768,
        324409786, 1476451891, 1236111477, 2281477571, 616879951],
    }

HIDENSEN = 12

canned_shuffles = {
    0: ['yojnpldsihgubxteczkqrfmwva', 'ivdleyxqpkhfmbcszwrugtjnao',
        'utcmjevqlxwyazbsdknpohfirg', 'rsbxdtcmepiqflyhzognjkvuwa',
        'vcmgphafiznqxlejuktdsorwby', 'pelsocnbhativxrfkwdjugmqzy',
        'hukoawzxjtbmdipgfrelcynqvs', 'yiltkvxpfmcuoghjazqerdbwns',
        'gkniojhfsamturzxwebycqvpdl', 'tfdykvzomnbuhplgcisejxqraw']
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
    12: (478950688.0, 479052512.0),
    }
assert HIDENSEN in n2chi

if 1:
    from mpmath import gammainc
    from math import factorial

    # To get this to work for large n!, had to add this to
    # mpmath\functions\hypergeometric.py" in _hyp1f1:
    #     kwargs['maxterms'] = 500_000
    def chi2(x, v):
        return float(gammainc(v/2, 0, x/2, True))

##    for n, (lo, hi) in n2chi.items():
##        v = factorial(n) - 1
##        print(n, "lo", chi2(lo, v))
##        print(n, "hi", chi2(hi, v))

units = (('d', 3600 * 24),
         ('h', 3600),
         ('m', 60),
        )

def format_seconds(s):
    result = []
    n, tenths = divmod(round(s * 10.0), 10)
    for tag, f in units:
        w, n = divmod(n, f)
        if w or result:
            result.extend((w, tag))
    result.extend((n, '.', tenths, 's'))
    return ''.join(map(str, result))

fint = lambda n: format(n, ",")

def get_period():
    x = START = 123
    p = 0
    target = target_inc = 100_000_000
    while True:
        p += 1
        if p >= target:
            print(fint(p), end="\r")
            target += target_inc
        x = (121525 * x + 386076519) & MASK32
        if x == START:
            break
    return p

def check(version):
    SEED = 42
    t = tinyrand.get(version, seed=SEED)
    assert t.NSTATES == 1 << t.BITS

    assert [t._get() for i in range(10)] == prefix[version]
    t.seed(SEED)
    assert [t._get() for i in range(10)] == prefix[version]
    t.seed(SEED + (123 << 32)) # xhwxk that only last 32 bits count
    assert [t._get() for i in range(10)] == prefix[version]

    try:
        t.seed(-1)
    except ValueError:
        pass
    else:
        raise ValueError("negative seed should have raised")

    letters = list('abcdefghijklmnopqrstuvwxyz')
    assert len(letters) == 26
    assert len(set(letters)) == 26

    def getone():
        xs = letters.copy()
        t.shuffle(xs)
        return ''.join(xs)

    expect = canned_shuffles[version]
    for trial in 1, 2:
        t.seed(SEED)
        got = [getone() for _ in range(len(expect))]
        assert got == expect, got

    print("checking period")
    p = get_period()
    print(fint(p))
    assert p == T32

from math import factorial, sqrt
from collections import defaultdict
from time import perf_counter as now

def makepc(hi):
    from itertools import islice
    pc = array.array('B', [0])
    todo = hi - 1
    while todo > 0:
        take = min(todo, len(pc))
        pc.extend(i + 1 for i in islice(pc, take))
        todo -= take
    return pc

N = 13
pc = makepc(2**N)
fac = [factorial(i) for i in range(N)]

def rank(p):
    result = present = 0
    for i, d in enumerate(reversed(p)):
        bit = 1 << d
        result += pc[present & (bit - 1)] * fac[i]
        present |= bit
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
    import array

    f = factorial(n)
    totaltrips = len(rng)
    freq = totaltrips / f
    st = f"{f=:,} {freq=:.2f} {rng=!r:} {totaltrips=:,} {try_all_seeds=:}"
    print(st)

    d = array.array('L', [0]) * f

    base = list(range(n))
    ntrips = 0
    limit = limit_inc = 2_000_000
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
        d[rank(xs)] += 1
    print("total time", format_seconds(now() - start_time), " " * 40)

    chisq = sum((got - freq)**2 for got in d) / freq
    df = f - 1
    sdev = sqrt(2.0 * df) or 1.0
    missing = d.count(0)
    if missing:
        print()
        print('*' * 50, missing, "missing")
        print()
    z = (chisq - df) / sdev
    p = chi2(chisq, df)
    st2 = f"{p:9.4%} v{t.VERSION} n{n} {df=} {chisq=:.2f} {sdev=:.2f} {z=:+.2f}"
    print(st2)
    if n in n2chi:
        print(st2, st, file=fout, flush=True)
        lo, hi = n2chi[n]
        assert lo < hi
        if lo <= chisq <= hi:
            print("in 5%-95% bounds", lo, "<=", chisq, "<=", hi)
        else:
            print()
            print("*** WARNING *** suspicious chi square ***")
            if lo > chisq:
                print(f"less than 5% bound {chisq} < {lo}")
                print()
            else:
                assert hi < chisq
                print(f"greater than 95% bound {chisq} > {hi}")

def check_chi3(t, n, freq, rng):
    import array

    totaltrips = len(rng)
    st = f"{freq=:.2f} {rng=!r:} {totaltrips=:,}"
    print(st)
    df = n - 1

    ds = [array.array('H', [0]) * n for i in range(n)]
    sdev = sqrt(2.0 * df) or 1.0

    base = list(range(n))
    ntrips = 0
    limit = limit_inc = 100_000_000 // n
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
        t.shuffle(xs)
        #assert sorted(xs) == base
        for i, j in enumerate(xs):
            ds[i][j] += 1
    print("total time", format_seconds(now() - start_time), " " * 40)

    for i, d in enumerate(ds):
        chisq = sum((got - freq)**2 for got in d) / freq
        z = (chisq - df) / sdev
        p = chi2(chisq, df)
        st2 = f"{p:9.4%} v{t.VERSION} n{n} pos{i} {df=} {chisq=:.2f} {sdev=:.2f} {z=:+.2f}"
        print(st2)
        print(st2, st, file=fout, flush=True)

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
        for n in range(1, HIDENSEN + 1):
            print("\nversion", version, "n", n)
            k = check_chi2(t, n, range(factorial(n) * 16))
            del k

def drive2(which):
    SPLIT = 9
    for version in tinyrand.SUPPORTED_VERSIONS:
        print("\nversion", version)
        t = tinyrand.get(version)
        if which == 1:
            n2s = {n : 0 for n in range(2, SPLIT)}
        elif which == 2:
            n2s = {n : 0 for n in range(SPLIT, HIDENSEN + 1)}
        else:
            assert False, which
        new_n2s = {}
        start_time = now()
        ATLEAST = 100_000_000
        didone = True
        while n2s:
            new_n2s.clear()
            for n, start in n2s.items():
                if start >= T32:
                    continue
                min_need = factorial(n) * 16
                stop = min(start + min_need, T32)
                if stop < T32:
                    if min_need < ATLEAST:
                        stop = min(start + ATLEAST, T32)
                    if T32 - stop < min_need:
                        stop = T32
                new_n2s[n] = stop
                print("\nversion", version, "n", n)
                check_chi2(t, n, range(start, stop), True)
                print("total elapsed", format_seconds(now() - start_time))
            n2s = new_n2s.copy()

# There's not enough TAM or time in the universe to exhaustively test
# "large" lists. 12 is the highest I can get away with. But we can do
# simple tests. Here, we shuffle range(n) n * F times. Then every
# element should appear in every position about F times. That can't
# catch many kinds of subtle problems, but does a great job at catching
# gross problems.

def drive3(seed=0):
    F = 50
    for version in tinyrand.SUPPORTED_VERSIONS:
        print("\nversion", version)
        t = tinyrand.get(version, seed)
        start_time = now()
        for n in itertools.chain(range(1, HIDENSEN + 1),
                                 [52, 100, 1000, 10000]):
            print("\nversion", version, "n", n)
            check_chi3(t, n, float(F), range(F * n))
        print("total elapsed", format_seconds(now() - start_time))

def bigdrive(read, which):
    import os
    global fout
    assert which in range(4)
    head = "/Code/"
    tail = f"fout{which}.txt"
    fn = head + tail
    if read:
        fd(fn)
        return
    tailbak = tail + ".bak"
    fnbak = head + tailbak
    if os.path.exists(fn):
        if os.path.exists(fnbak):
            print("removing", fnbak)
            os.remove(fnbak)
        print("renaming", fn, "to", fnbak)
        os.rename(fn, fnbak)
    fout = open(fn, "w")
    if which == 0:
        drive()
    elif which == 3:
        drive3()
    else:
        drive2(which)
    fout.close()

def fd(fn):
    bins = [0] * 20
    with open(fn) as f:
        for line in f:
            first = line.split(maxsplit=1)[0]
            assert first.endswith('%')
            p = float(first[:-1])
            bins[int(p / 5.0)] += 1
    tot = sum(bins)
    df = len(bins) - 1
    freq = tot / len(bins)
    chisq = sum((freq - got) ** 2 / freq for got in bins)
    print(bins)
    print(f"{tot=} {df=} {freq=} {chisq=} {chi2(chisq, df)=}")

if __name__ == "__main__":
    import sys
    which = 0
    if len(sys.argv) > 1:
        read = sys.argv[1] == "r"
        if read:
            del sys.argv[1]
        if len(sys.argv) > 1:
           which = int(sys.argv[1])
    start = now()
    bigdrive(read, which)
    print("total elapsed", format_seconds(now() - start))
