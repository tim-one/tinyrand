Very simple code for shuffling short lists.

The initial code is in Python, but is self-contained, uses no Python-specific
features, no Python libraries, no floats, and creates no ints larger than
32 bits.

The intent is that it be easy to recode in any language for any non-trivial
platform, and generate identical results on all.

The driving use case is for "last resort" tie-breaking in election scoring
systems. In those, a randomly permuted list of candidates can be established,
and if there's no other way to break a tie, candidate C beats D
if and only if C appears before D in the list. In Python:

```python
import tinyrand
# `tiebreaker` is a list of candidates
tiebreaker.sort() # start with deterministic order
t = tinyrand.get(seed=some_integer_seed) # use default version
t.shuffle(tiebreaker)
```

Speed isn't important here. Code simplicity, portability, and reproducibilty
are. Quality of results isn't especially important either. If all
permutations of lists of length <= 10 are about equally likely, "good enough".

## Versions

- 0: 32-bit state, and no int larger than a 32-bit unsigned int is created.
All implementations should support version 0.


## Python docs

`tinyrand` supplies a few constants and a factory function.

### Module level

- `tinyrand.SUPPORTED_VERSIONS`

    A tuple of supported version numbers (small integers) in sorted order.

- `tinyrand.DEFAULT_VERSION`

    The version returned if a version isn't passed to `get()`.

- `tinyrand.get(version=tinyrand.DEFAULT_VERSION, seed=0)`

    Return an object that can be used for shuffling.

    `version` is an integer in SUPPORTED_VERSIONS.

    `seed` is an integer >= 0 used to initialize the internal random number
generator's state. Only the trailing bits are used - the state is typically
very small.

    It's intended that results be exactly reproducible "forever", across all
implementations, for objects created with the same `version`and `seed`.

### Instance objects

After `t = tinyrand.get(...)`, `t` has one method of primary interest:

- `t.shuffle(xs)`

    `xs` is a list, which is randomly permuted in place. `None` is returned,
as is the usual case for Python's mutating functions.

    `ValueError` is raised if `len(xs) > t.NSTATES`. This can't be used for very
long lists. In the context of elections, this isn't a real limitation.

Of less interest,

- `t.seed(seed)`

    Sets `t`'s  state to the same as if it had just been created by `.get()`
with the same `seed`.

It also has a few constants of minor interest:

- `t.VERSION`

    The version argument passed to `.get()`.

- `t.BITS`

    The number of internal basic state bits.

- `t.NSTATES`

    The number of internal basic states == `2 ** t.BITS`.
