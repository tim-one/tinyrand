Very simple code for shuffling short lists.

The initial code is in Python, but is self-contained, uses no Python-specific
features, no Python libraries, no floats, and stores no ints larger than
32 bits. Intermediate results only care about the last 32 bits. uint32_t
suffices in C; in Python they're masked to the least-significant 32 bits;
in JavaScript no intermediate is wider than 50 bits, so are computed
exactly using IEEE-754 doubles.

The intent is that it be easy to recode in any language for any non-trivial
platform, and generate identical results on all.

The driving use case is for "last resort" tie-breaking in election scoring
systems. In those, a randomly permuted list of candidates can be established,
and if there's no other way to break a tie, candidate C beats D
if and only if C appears before D in the list. In Python:

```python
import tinyrand
# `tiebreaker` is a list of candidates.
# This must be in a fixed (but arbitrary) order.
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
no larger than 32 bits.

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

    The number of trailing bits used in a seed.

- `t.NSTATES`

    The total number of distinct seeds = 2<sup>BITS</sup>.

## Testing a new implementation

Create a version 0 object (function, whatever) seeded with 42. Then
get the first 10 outputs with the implementation's version of `._get()`.
The results must be:

<pre>
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
</pre>

Then (re)seed it with 42, and try again. It should deliver the same
10 results.

In Python,

```python
>>> t = tinyrand.get(0, 42)
>>> [t._get() for i in range(10)]
[2975584321, 1915941066, 2870739003, 2578514367, 4127658768, 324409786, 1476451891, 1236111477, 2281477571, 616879951]
>>> t.seed(42)
>>> [t._get() for i in range(10)]
[2975584321, 1915941066, 2870739003, 2578514367, 4127658768, 324409786, 1476451891, 1236111477, 2281477571, 616879951]
```

You ran also check these permuations:

```python
>>> t =tinyrand.get(0, 42)
>>> t.seed(42)
>>> for i in range(10):
...     xs = list(range(20))
...     t.shuffle(xs)
...     print(xs)
...
[5, 14, 9, 13, 15, 11, 3, 18, 8, 7, 6, 17, 1, 12, 19, 4, 2, 0, 10, 16]
[16, 14, 9, 13, 0, 4, 12, 19, 10, 11, 8, 1, 15, 5, 2, 3, 6, 17, 18, 7]
[11, 6, 14, 13, 4, 5, 3, 17, 12, 10, 0, 9, 2, 7, 18, 1, 16, 8, 15, 19]
[19, 18, 7, 14, 4, 0, 6, 5, 9, 8, 3, 16, 2, 11, 10, 17, 15, 1, 13, 12]
[16, 10, 12, 15, 8, 4, 6, 13, 0, 7, 2, 19, 5, 11, 18, 9, 14, 3, 1, 17]
[7, 10, 2, 17, 13, 4, 3, 11, 12, 8, 6, 9, 15, 1, 18, 16, 19, 0, 5, 14]
[13, 4, 7, 19, 0, 18, 15, 1, 12, 17, 5, 2, 10, 6, 9, 14, 11, 16, 8, 3]
[13, 6, 9, 16, 12, 0, 14, 15, 1, 5, 17, 8, 18, 3, 11, 2, 7, 19, 10, 4]
[9, 5, 12, 6, 1, 10, 3, 18, 11, 14, 16, 15, 13, 4, 7, 0, 2, 19, 17, 8]
[3, 14, 12, 1, 18, 6, 11, 9, 17, 5, 15, 8, 0, 7, 16, 2, 13, 4, 10, 19]
```
