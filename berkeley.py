clocks = {"M": 200, "A": 180, "B": 250}

avg = sum(clocks.values()) / 3

for n in clocks:
    delta = avg - clocks[n]
    clocks[n] += delta
    print(n, "adjust by", delta)