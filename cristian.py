
real = 1000


class Server:
    def clock(self):
        return real


class Client:
    def __init__(self, offset):
        self.offset = offset

    def clock(self):
        return real + self.offset


def sync(c, delay_out, delay_back):
    global real

    t0 = c.clock()

    real += delay_out
    print(real)

    T = server.clock()

    real += delay_back
    print(real)

    t1 = c.clock()

    est = T + (t1 - t0) / 2

    c.offset = est - real

    print(
        f"estimate={est}, real={real}, "
        f"error={est - real}"
    )


server = Server()

sync(Client(-900), 10, 10)
sync(Client(-900), 18, 2)
