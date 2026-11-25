
names = ["A", "B", "C"]


class Node:
    def __init__(self, name):
        self.i = names.index(name)
        self.name = name
        self.v = [0, 0, 0]
        self.buf = []

    def broadcast(self, text):
        self.v[self.i] += 1

        return {
            "text": text,
            "from": self.i,
            "v": self.v.copy()
        }

    def recv(self, m):
        self.buf.append(m)
        self.flush()

    def ok(self, m):
        return (
            self.v[m["from"]] == m["v"][m["from"]] - 1
            and all(
                x <= self.v[k]
                for k, x in enumerate(m["v"])
                if k != m["from"]
            )
        )

    def flush(self):
        while True:
            m = next(
                (x for x in self.buf if self.ok(x)),
                None
            )

            if m is None:
                break

            self.buf.remove(m)
            self.v[m["from"]] += 1

            print(
                f"{self.name} delivered {m['text']}, "
                f"v={self.v}"
            )


A = Node("A")
B = Node("B")
C = Node("C")

m1 = A.broadcast("m1")
B.recv(m1)

m2 = B.broadcast("m2")
C.recv(m2)

print("C buffer:", len(C.buf))

C.recv(m1)

m3 = C.broadcast("m3")
A.recv(m3)

print("A buffer:", len(A.buf))

A.recv(m2)
