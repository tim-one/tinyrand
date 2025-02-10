# Don't use "advanced" Python features here - clarity is prized. It's
# intended that it work under any Python release in the Python 3 line.
# On a 64-bit box, it even runs under Python 2.7.11, although Python 2
# compatibility is not a goal and may not be maintained.

SUPPORTED_VERSIONS = (0,)
DEFAULT_VERSION = 0
assert DEFAULT_VERSION in SUPPORTED_VERSIONS

MASK32 = 0xffffffff

class TinyRandBase:
    VERSION = None  # subclass must override
    BITS = 32       # number of seed bits

    def __init__(self, seed=0):
        assert self.BITS >= 16
        self.NSTATES = 1 << self.BITS
        self.MASK = self.NSTATES - 1

        self.seed(seed)

    # Subclass must override
    def seed(self):
        raise NotImplementedError

    # Subclass must supply this, Note that NSTATES == 2**BITS,
    # and BITS must be >= 16.
    def _get(self):
        """Return a random iot in range(NSTATES)."""

        raise NotImplementedError

    # A "forward" version of Fisher-Yates. Python's `shuffle()` is the
    # more common "backward" version, but that benefits a lot from
    # Python's int.bit_length() method. The forward version doesn't need
    # that.
    def shuffle(self, a):
        """Permute list `a` in-place, leaving it in a random order."""
        if len(a) > self.NSTATES:
            raise ValueError("list too long", len(a))
        shift = self.BITS - 1
        hi = 2
        for j in range(1, len(a)):
            # Invariant: the first j elements are randomly permuted.
            # Extend that by swapping a[j] with one of first j+1 elements.
            # The element to swap is picked by an unbiased accept/reject
            # method: pick an index "at random" until finding one <= j.
            if j == hi:
                hi <<= 1
                shift -= 1
##            while (i := self._get() >> shift) > j:
##                pass # typically executed at most once
            while True: # typically no more than 2 iterations
                i = self._get() >> shift
                if i <= j:
                    break
            a[i], a[j] = a[j], a[i]

class TinyRand0(TinyRandBase):
    VERSION = 0

##    # xorshift32 from https://en.wikipedia.org/wiki/Xorshift
##    # Note that 0 isn't a possible output. In context that
##    # doesn't matter.
##    # The period is 2**32 - 1, and across the period each int in
##    # range(1, 2**32) is produced once.
##    # The low-order bits aren't high quality. In context that doesn't
##    # matter, because .getrandbits() only uses high-order bits of
##    # each result.
##    def _get(self):
##        x = self.state
##        x ^= (x << 13) & MASK32
##        x ^= x >> 17
##        x ^= (x << 5) & MASK32
##        self.state = x
##        return x

    # Marsaglia's xorshift128. A strong generator of 32-bit ints using
    # 128 bits of state. Period is 2**128 - 1 ~= 3.4e38,  It fails some
    # statistical tests that are irrelevent to us (like rank of random
    # large matricss in GF(2), which almost all bit-fiddling generators
    # fail (including the Mersenne Twister!)).
    #
    # Source code from Marsaglia's paper:
    #
    # unsigned long xor128(){
    # static unsigned long x=123456789,y=362436069,z=521288629,w=88675123;
    # unsigned long t;
    # t=(x^(x<<11));x=y;y=z;z=w; return( w=(w^(w>>19))^(t^(t>>8)) );

    def _get(self):
        state = self.state
        x = state[0]
        x ^= (x << 11) & MASK32
        x ^= x >> 8
        state[0] = state[1]
        state[1] = state[2]
        state[2] = w = state[3]
        w ^= (w >> 19) ^ x
        state[3] = w
        return w

    def seed(self, seed=0):
        if seed < 0:
            raise ValueError("seed must be >= 0", seed)
        seed &= MASK32
        state = self.state = [0, 0, 0, 0]
        # Initialize with an ordinary LCG.
        # The multiplier does well on the spectral test, but more
        # importantly fits in 17 bits. THe product therefore fits in 49
        # bits, so will be computed exactly in languages that only use
        # IEEE-754 doubles as their "number" type.
        for i in range(4):
            state[i] = seed = (121525 * seed + 386076519) & MASK32

        # While this is a good PRNG, initialization is delicate, trying
        # to spray a 32-bit seed across 128 bits of state. While it's
        # fine as-is, there are nevertheless visible correlations across
        # the first few outputs given seeds that are close together,
        # i.e. like seed and seed+1. Running the generator a handful of
        # times does a much better job of scrambling the full state.
        for i in range(6):
            self._get()

def get(version=DEFAULT_VERSION, seed=0):
    if version not in SUPPORTED_VERSIONS:
        raise ValueError("invalid version", version,
                         "must be in", SUPPORTED_VERSIONS)
    t =(TinyRand0,
       )[version](seed)
    assert version == t.VERSION
    return t

# All the rest is Python-specific quick doctests.

error_tests = """
>>> t = get(version=666)
Traceback (most recent call last):
   ...
ValueError: ('invalid version', 666, 'must be in', (0,))
>>> t = get(seed=-1)
Traceback (most recent call last):
    ...
ValueError: ('seed must be >= 0', -1)
"""

inner_gen_tests = """
>>> SEED = 42
>>> t = get(0, SEED)
>>> for i in range(10):
...     print(t._get())
2975584321
1915941066
2870739003
2578514367
4127658768
324409786
1476451891
1236111477
2281477571
616879951
>>> t.seed(SEED) # ensure it's repeatable
>>> for i in range(10):
...     print(t._get())
2975584321
1915941066
2870739003
2578514367
4127658768
324409786
1476451891
1236111477
2281477571
616879951
>>> t.seed((1 << 31) + 12345) # try a 32-bit seed
>>> for i in range(10):
...     print(t._get())
650780454
2308137737
1986895561
420836754
1867541177
2110375793
1732806103
3577992521
967469306
174838513
>>> t.seed(SEED + (137 << 32)) # high-order bits stripped?
>>> for i in range(5):
...     print(t._get())
2975584321
1915941066
2870739003
2578514367
4127658768
"""

perm_tests = """
>>> letters = list('abcdefghijklmnopqrstuvwxyz')
>>> len(letters)
26
>>> len(set(letters))
26
>>> SEED = 42
>>> t = get(0, SEED)
>>> def getone():
...     xs = letters[:]
...     t.shuffle(xs)
...     return ''.join(xs)
>>> for i in range(10):
...     print(getone())
yojnpldsihgubxteczkqrfmwva
ivdleyxqpkhfmbcszwrugtjnao
utcmjevqlxwyazbsdknpohfirg
rsbxdtcmepiqflyhzognjkvuwa
vcmgphafiznqxlejuktdsorwby
pelsocnbhativxrfkwdjugmqzy
hukoawzxjtbmdipgfrelcynqvs
yiltkvxpfmcuoghjazqerdbwns
gkniojhfsamturzxwebycqvpdl
tfdykvzomnbuhplgcisejxqraw
>>> t.seed(SEED) # and repeat
>>> for i in range(10):
...     print(getone())
yojnpldsihgubxteczkqrfmwva
ivdleyxqpkhfmbcszwrugtjnao
utcmjevqlxwyazbsdknpohfirg
rsbxdtcmepiqflyhzognjkvuwa
vcmgphafiznqxlejuktdsorwby
pelsocnbhativxrfkwdjugmqzy
hukoawzxjtbmdipgfrelcynqvs
yiltkvxpfmcuoghjazqerdbwns
gkniojhfsamturzxwebycqvpdl
tfdykvzomnbuhplgcisejxqraw
"""

__test__ = {
    "err": error_tests,
    "_get": inner_gen_tests,
    "perm": perm_tests,
}

if __name__ == "__main__":
    import doctest
    doctest.testmod()
