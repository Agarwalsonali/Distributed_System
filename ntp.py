
real = 1000


class Server:
    def clock(self):
        return real


class Client:
    def __init__(self, offset):
        self.offset = offset

    def clock(self):
        return real + self.offset


def sync(c, out, proc, back):
    global real

    t0 = c.clock()

    real += out
    t1 = server.clock()

    real += proc
    t2 = server.clock()

    real += back
    t3 = c.clock()

    offset = ((t1 - t0) + (t2 - t3)) / 2

    delay = (t3 - t0) - (t2 - t1)

    c.offset += offset

    print({
        "offset": offset,
        "delay": delay,
        "error": c.clock() - real
    })


server = Server()

sync(Client(-50), 10, 4, 10)
sync(Client(-50), 2, 4, 18)
sync(Client(-50), 2, 100, 18)
