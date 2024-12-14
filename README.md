Very simple code for shuffling short lists.

The initial code is in Python, but is self-contained, uses no Python-specific features, no Python libraries, no floats, and creates no ints larger than 32 bits.

The intent is that it be easy to recode in any language for any non-trivial platform, and generate identical results on all.

The driving use case is for "last resort" tie-breaking in election scoring systems. In those, a randomly permuted list of candidates can be established, and
if there's no other way to break a tie, candidate C beats D if and only if C appears before D in the list. In Python:

```python
# cands is a list of candidates.
cands.sort() # start with deterministic order
t = TinyRand(some_integer_seed)
t.shuffle(cands)
```

Speed isn't important here. Code simplicity, portability, and reproducibilty are. Quality of results isn't especially important either. If all permutations of
lists of length <= 10 are about equally likely, "good enough".

