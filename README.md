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

In general, the more bits in the state, the higher quality the results.

- 0: 16-bit state, and no int larger than a 32-bit unsigned int is created.
All implementations should support version 0.

- 1: 26-bit state, and no int larger than a 52-bit unsigned int is created.
This is for languages that use IEEE-754 "double precision" floats as their
native "number" type, where unsgined ints through 53 bits can be represented
exactly,

## Python docs

`tinyrand` supplies a few constants and a factory function.

### Module level

- `tinyrand.get(version=tinyrand.DEFAULT_VERSION, seed=0)`

    Return an object that can be used for shuffling.
    The version is an integer between 0 and `tinyrand.MAX_VERSION`
inclusive, It's intended that results be exactly reproducible "forever",
across all implementations, for objects created with the same `version`
and `seed`.
    `seed` is an integer >= 0 used to initialize the internal random number
generator's state. Only the trailing bits are used - the state is typically
very small.

- `tinyrand.MAX_VERSION`

    The largest version implemented.

- `tinyrand.DEFAULT_VERSION`

    The version returned if a version isn't passed to `get()`.

- `tinyrand.SUPPORTED_VERSIONS`

    List of all supported versions.

### Instance objects

After `t = tinyrand.get(...)`, `t` has one method of primary interest:

- `t.shuffle(xs)`

    `xs` is a list, which is randomly permuted in place. `None` is returned,
as is the usual case for Python's mutating functions.

Of less interest,

- `t.seed(seed)`

    Sets `t`'s  state to the same as if it had just been created by `.get()`
with the same `seed`.

It also has a few constants of minor interest:

- `t.VERSION`

    The version argument passed to `.get()`.

- `t.BITS`

    The number of internal state bits.
