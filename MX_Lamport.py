
import json

names = ["A", "B", "C"]
nodes = {}
wire = []


def pump():
    while wire:
        m = wire.pop(0)
        nodes[m["to"]].recv(m)


class Node:
    def __init__(self, name):
        self.name = name
        self.t = 0
        self.q = []
        self.replies = 0
        self.want = False

        nodes[name] = self

    def send(self, to, msg_type):
        wire.append({
            "to": to,
            "type": msg_type,
            "ts": self.t,
            "from": self.name
        })

    def others(self):
        return [n for n in names if n != self.name]

    def sortQ(self):
        self.q.sort(key=lambda x: (x[0], x[1]))

    def request(self):
        self.t += 1
        self.want = True
        self.replies = 0

        self.q.append([self.t, self.name])

        for n in self.others():
            self.send(n, "REQ")

    def recv(self, m):
        self.t = max(self.t, m["ts"]) + 1

        if m["type"] == "REQ":
            self.q.append([m["ts"], m["from"]])
            self.sortQ()

            self.t += 1
            self.send(m["from"], "REPLY")

        if m["type"] == "REPLY":
            self.replies += 1

        if m["type"] == "REL":
            self.q = [
                r for r in self.q
                if r[1] != m["from"]
            ]

        self.tryEnter()

    def tryEnter(self):
        self.sortQ()

        if (
            self.want
            and self.replies == len(names) - 1
            and self.q[0][1] == self.name
        ):
            print(
                f"{self.name} ENTERS CS, "
                f"queue={json.dumps(self.q)}"
            )

            self.release()

    def release(self):
        self.q = [
            r for r in self.q
            if r[1] != self.name
        ]

        self.want = False
        self.t += 1

        for n in self.others():
            self.send(n, "REL")

        print(f"{self.name} releases")


# Create nodes
A = Node("A")
B = Node("B")
C = Node("C")

# Initialize logical clocks
A.t = 4
C.t = 3

# Send requests
A.request()
C.request()

print(wire)

# Deliver all messages
pump()
