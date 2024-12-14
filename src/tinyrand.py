# Very simple 16-bit PRNG, self-contained, and needing nothing fancier
# than 16x16->32 bit unsigned integer multiplication.

BITS = 16
MASK = (1 << BITS) - 1

# Table for Bays-Durham shuffle.
BD_BITS = 7
assert BD_BITS <= BITS
BD_SIZE = 1 << BD_BITS
BD_MASK = BD_SIZE - 1

class TinyRandBase:
    def __init__(self, seed=0):
        self.seed(seed)

    def seed(self, seed):
        self.seed = seed & MASK
        self.tab = [self._get() for i in range(BD_SIZE)]
        self.result = self._get()

    # Subclass must supply this,
    def _get(self):
        """Return a random iot in range(2**16).

        The period is 2**16, and each possible result appears once
        across the period.
        """

        raise NotImplementedError

    # Bays-Durham shuffle of the base LCG. This increases the period
    # and breaks up the extreme regularity of the LCG's low-order bits.
    def get(self):
        i = self.result & BD_MASK
        self.result = self.tab[i]
        self.tab[i] = self._get()
        return self.result

    # Return random int that fits in at most `n` bits.
    # IOW, a random int in range(2**n).
    # 1 <= n <= BITS required. In context, this is meant to be a helper
    # for `shuffle()`. Of course it _could_ bw made fancier.
    def getrandbits(self, n):
        assert 1 <= n <= BITS
        return self.get() >> (BITS - n)

    # A "forward" version of Fisher-Yates. Python's `shuffle()` is the
    # more common "backward" version, but that benefits a lot from
    # Python's int.bit_length() methed. The forward version doesn't need
    # that (`bits` below tracks the needed bit length as `j` increases).
    def shuffle(self, a):
        """Permute list `a` in-place, leaving it in a random order."""
        if len(a) >= MASK + 1:
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

class TinyRand(TinyRandBase):
    def __init__(self, seed=0):
        super().__init__(seed)

    def _get(self):
        # An ordinary LCG.
        # 43317 came from a table of multipliers with "goad" spectral
        # scores,
        self.seed = (self.seed * 43317 + 1) & MASK
        # A PCG-like trick to permute the output space, destroying the
        # extreme regularity across the sequence of low-order bits
        return self.seed ^ (self.seed >> 7)
