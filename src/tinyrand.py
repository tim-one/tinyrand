SUPPORTED_VERSIONS = (0,)
DEFAULT_VERSION = 0
assert DEFAULT_VERSION in SUPPORTED_VERSIONS

MASK32 = (1 << 32) - 1

class TinyRandBase:
    VERSION = None  # subclass must override
    BITS = 32       # number of state bits
##    BD_BITS = 4     # table for Bays-Durham shuffle
##    BD_SIZE = 1 << BD_SIZE
    def __init__(self, seed=0):
        assert self.BITS >= 16
        self.NSTATES = 1 << self.BITS
        self.MASK = self.NSTATES - 1
##        assert self.BD_BITS <= self.BITS
##        self.BD_SIZE = 1 << self.BD_BITS
##        self.BD_MASK = self.BD_SIZE - 1

        self.seed(seed)

    # Subclass must override
    def seed(self):
        raise NotImplementedError
##        self.tab = [self._get() for i in range(self.BD_SIZE)]
##        self.result = self._get()

    # Subclass must supply this, Note that NSTATES == 2**BITS,
    # and BITS must be >= 16.
    def _get(self):
        """Return a random iot in range(NSTATES)."""

        raise NotImplementedError

##    # Bays-Durham shuffle of the base LCG. This increases the period
##    # and breaks up the extreme regularity of the LCG's low-order bits.
##    def get(self):
##        result = self.result
##        i = result & self.BD_MASK
##        self.result = self.tab[i]
##        self.tab[i] = self._get()
##        return result
##
##    # Return random int that fits in at most `n` bits.
##    # IOW, a random int in range(2**n).
##    # 1 <= n <= BITS required. In context, this is meant to be a helper
##    # for `shuffle()`. Of course it _could_ bw made fancier.
##    def getrandbits(self, n):
##        assert 1 <= n <= self.BITS
##        return self._get() >> (self.BITS - n)

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
            while (i := self._get() >> shift) > j:
                pass # typically executed at most once
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
    # t=(xˆ(x<<11));x=y;y=z;z=w; return( w=(wˆ(w>>19))ˆ(tˆ(t>>8)) );

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
        # bits, so will ne computed exactly in languages that only use
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

##        super().seed()

def get(version=DEFAULT_VERSION, seed=0):
    if version not in SUPPORTED_VERSIONS:
        raise ValueError("invalid version", version,
                         "must be in", SUPPORTED_VERSIONS)
    t =(TinyRand0,
       )[version](seed)
    assert version == t.VERSION
    return t
