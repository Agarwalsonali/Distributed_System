
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
        self.state = "IDLE"
        self.myTs = 0
        self.replies = 0
        self.deferred = []

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

    def iAmFirst(self, m):
        return (
            self.myTs < m["ts"]
            or (
                self.myTs == m["ts"]
                and self.name < m["from"]
            )
        )

    def request(self):
        self.t += 1
        self.state = "WANT"
        self.myTs = self.t
        self.replies = 0

        for n in self.others():
            self.send(n, "REQ")

    def recv(self, m):
        self.t = max(self.t, m["ts"]) + 1

        if m["type"] == "REQ":

            defer = (
                self.state == "CS"
                or (
                    self.state == "WANT"
                    and self.iAmFirst(m)
                )
            )

            if defer:
                self.deferred.append(m["from"])
            else:
                self.send(m["from"], "REPLY")

        else:
            self.replies += 1

        if (
            self.state == "WANT"
            and self.replies == len(names) - 1
        ):
            self.enter()

    def enter(self):
        self.state = "CS"
        print(f"{self.name} ENTERS")

        # Critical section body
        self.state = "IDLE"

        print(
            f"{self.name} exits, sending deferred "
            f"replies to {self.deferred}"
        )

        for n in self.deferred:
            self.send(n, "REPLY")

        self.deferred = []


# Create nodes
A = Node("A")
B = Node("B")
C = Node("C")

# Initialize logical clocks
A.t = 4
C.t = 3

# Both processes request the critical section
A.request()
C.request()

# Deliver all messages
pump()
