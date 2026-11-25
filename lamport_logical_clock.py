
net = {}


class Node:
    def __init__(self, name):
        self.name = name
        self.t = 0
        net[name] = self

    def send(self, to, text):
        self.t += 1

        print(
            f"{self.name} -> {to}: {text} "
            f"(t={self.t})"
        )

        net[to].recv(text, self.name, self.t)

    def recv(self, text, from_node, ts):
        self.t = max(self.t, ts) + 1

        print(
            f'{self.name} got "{text}" from '
            f'{from_node} (t={self.t})'
        )


A = Node("A")
B = Node("B")
C = Node("C")

print(net)

A.send("B", "hello")
A.send("C", "this is from A")
C.send("B", "hi B, this is C")
