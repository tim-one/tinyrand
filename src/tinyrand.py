# Very simple 16-bit PRNG, self-contained, and needing nothing fancier
# than 16x16->32 bit unsigned integer multiplication.

DEFAULT_VERSION = 0
SUPPORTED_VERSIONS = (0,)
assert DEFAULT_VERSION in SUPPORTED_VERSIONS

MASK32 = (1 << 32) - 1

class TinyRandBase:
    VERSION = None  # subclass must override
    BITS = 32       # number of state bits
    BD_BITS = 7     # table for Bays-Durham shuffle

    def __init__(self, seed=0):
        assert self.BITS >= 16
        self.NSTATES = 1 << self.BITS
        self.MASK = self.NSTATES - 1
        assert self.BD_BITS <= self.BITS
        self.BD_SIZE = 1 << self.BD_BITS
        self.BD_MASK = self.BD_SIZE - 1

        self.seed(seed)

    def seed(self, seed):
        if seed < 0:
            raise ValueError("seed must be >= 0", seed)
        self.state = seed & self.MASK
        self.tab = [self._get() for i in range(self.BD_SIZE)]
        self.result = self._get()

    # Subclass must supply this, Note that NSTATES == 2**BITS,
    # and BITS must be >= 16.
    def _get(self):
        """Return a random iot in range(NSTATES)."""

        raise NotImplementedError

    # Bays-Durham shuffle of the base LCG. This increases the period
    # and breaks up the extreme regularity of the LCG's low-order bits.
    def get(self):
        result = self.result
        i = result & self.BD_MASK
        self.result = self.tab[i]
        self.tab[i] = self._get()
        return result

    # Return random int that fits in at most `n` bits.
    # IOW, a random int in range(2**n).
    # 1 <= n <= BITS required. In context, this is meant to be a helper
    # for `shuffle()`. Of course it _could_ bw made fancier.
    def getrandbits(self, n):
        assert 1 <= n <= self.BITS
        return self.get() >> (self.BITS - n)

    # A "forward" version of Fisher-Yates. Python's `shuffle()` is the
    # more common "backward" version, but that benefits a lot from
    # Python's int.bit_length() method. The forward version doesn't need
    # that (`bits` below tracks the needed bit length as `j` increases).
    def shuffle(self, a):
        """Permute list `a` in-place, leaving it in a random order."""
        if len(a) > self.NSTATES:
            raise ValueError("list too long", len(a))
        bits = 1
        hi = 2
        for j in range(1, len(a)):
            # Invariant: the first j elements are randomly permuted.
            # Extend that by swapping a[j] with one of first j+1 elements.
            # The element to swap is picked by an unbiased accept/reject
            # method: pick an index "at random" until finding one <= j.
            if j == hi:
                hi <<= 1
                bits += 1
            while (i := self.getrandbits(bits)) > j:
                pass # typically executed at most once
            a[i], a[j] = a[j], a[i]

class TinyRand0(TinyRandBase):
    VERSION = 0

    # xorshift32 from https://en.wikipedia.org/wiki/Xorshift
    # Note that 0 isn't a possible output. In context that
    # doesn't matter.
    # The period is 2**32 - 1, and across the period each int in
    # range(1, 2**32) is produced once.
    # The low-order bits aren't high quality. In context that doesn't
    # matter, because .getrandbits() only uses high-order bits of
    # each result.
    def _get(self):
        x = self.state
        x ^= (x << 13) & MASK32
        x ^= x >> 17
        x ^= (x << 5) & MASK32
        self.state = x
        return x

    # Must avoid a 0 state. 0 ia a fixed point of ._get().
    def seed(self, seed=0):
        super().seed(seed or 1)
        if not self.state:
            super().seed(1)

def get(version=DEFAULT_VERSION, seed=0):
    if version not in SUPPORTED_VERSIONS:
        raise ValueError("invalid version", version,
                         "must be in", SUPPORTED_VERSIONS)
    t =(TinyRand0,
       )[version](seed)
    assert version == t.VERSION
    return t
