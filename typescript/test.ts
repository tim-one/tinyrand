import { get } from "./tinyrand";

describe("TinyRand", () => {
  test("_get() produces expected sequence", () => {
    const SEED = 42;
    const t = get(0, SEED);

    const expected = [
      2975584321,
      1915941066,
      2870739003,
      2578514367,
      4127658768,
      324409786,
      1476451891,
      1236111477,
      2281477571,
      616879951,
    ];

    for (let i = 0; i < 10; i++) {
      expect(t._get()).toBe(expected[i]);
    }

    // Test repeatability with same seed.
    t.seed(SEED);
    for (let i = 0; i < 10; i++) {
      expect(t._get()).toBe(expected[i]);
    }
  });

  test("shuffle produces expected permutation", () => {
    const SEED = 42;
    const t = get(0, SEED);

    const expected = [
      "yojnpldsihgubxteczkqrfmwva",
      "ivdleyxqpkhfmbcszwrugtjnao",
      "utcmjevqlxwyazbsdknpohfirg",
      "rsbxdtcmepiqflyhzognjkvuwa",
      "vcmgphafiznqxlejuktdsorwby",
      "pelsocnbhativxrfkwdjugmqzy",
      "hukoawzxjtbmdipgfrelcynqvs",
      "yiltkvxpfmcuoghjazqerdbwns",
      "gkniojhfsamturzxwebycqvpdl",
      "tfdykvzomnbuhplgcisejxqraw",
    ];

    function getOnePermutation(): string {
      const letters = "abcdefghijklmnopqrstuvwxyz".split("");
      t.shuffle(letters);
      return letters.join("");
    }

    for (let i = 0; i < 10; i++) {
      expect(getOnePermutation()).toBe(expected[i]);
    }

    // Test repeatability: reset the seed and try again.
    t.seed(SEED);
    for (let i = 0; i < 10; i++) {
      expect(getOnePermutation()).toBe(expected[i]);
    }
  });

  test("error cases", () => {
    expect(() => get(666)).toThrow("Invalid version");
    expect(() => get(0, -1)).toThrow("Seed must be >= 0");

    const t = get(0, 42);
    // Create an array that is "too long" (length greater than NSTATES, which is 65536).
    const tooLongArray = new Array(Math.pow(2, 20)).fill(0);
    expect(() => t.shuffle(tooLongArray)).toThrow("List too long");
  });
});