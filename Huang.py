
import socket
import threading
import time
import sys
from collections import defaultdict

HOST = "127.0.0.1"
BASE_PORT = 6001
EPSILON = 1.0e-7
CONNECT_TIMEOUT = 2.5
READ_TIMEOUT = 3.0


class Huang:
    def __init__(self, node_id, total_nodes):
        self.id = node_id
        self.total_nodes = total_nodes
        self.port = BASE_PORT + node_id

        self.lock = threading.RLock()

        # Local tree configuration
        self.parent = -1
        self.children = set()
        self.tree_version = -1

        # Root's complete topology
        self.parent_of = [-1] * total_nodes
        self.children_of = [set() for _ in range(total_nodes)]
        self.root_tree_version = 0

        # Credit and computation state
        self.controller_weight = 1.0
        self.weight = 0.0

        self.active = False
        self.started = False
        self.terminated = False
        self.resetting = False

        self.round = 1

        self.outstanding_children = set()
        self.reset_ack_nodes = set()

        self.running = True

    # --------------------------------------------------
    # BASIC UTILITIES
    # --------------------------------------------------

    def node_name(self, node):
        return f"Node {node}"

    def port_for(self, node):
        return BASE_PORT + node

    def valid_node(self, node):
        return 0 <= node < self.total_nodes

    # --------------------------------------------------
    # TCP SERVER
    # --------------------------------------------------

    def start_server(self):
        server_thread = threading.Thread(
            target=self.server_loop,
            daemon=True
        )
        server_thread.start()

    def server_loop(self):
        try:
            with socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            ) as server:

                server.setsockopt(
                    socket.SOL_SOCKET,
                    socket.SO_REUSEADDR,
                    1
                )

                server.bind((HOST, self.port))
                server.listen()

                print(
                    f"Node {self.id} TCP server "
                    f"listening on port {self.port}"
                )

                while self.running:
                    try:
                        client, address = server.accept()

                        handler = threading.Thread(
                            target=self.handle_socket,
                            args=(client,),
                            daemon=True
                        )

                        handler.start()

                    except OSError:
                        if self.running:
                            raise

        except OSError as error:
            if self.running:
                print(
                    f"Could not start server on port "
                    f"{self.port}: {error}"
                )
                self.running = False

    def handle_socket(self, client):
        try:
            with client:
                client.settimeout(READ_TIMEOUT)

                data = client.makefile("r")
                output = client.makefile("w")

                message = data.readline().strip()

                if not message:
                    response = "ERROR|EMPTY"
                else:
                    response = self.receive(message)

                output.write(response + "\n")
                output.flush()

        except OSError as error:
            print(f"TCP handler error: {error}")

    # --------------------------------------------------
    # TCP CLIENT
    # --------------------------------------------------

    def send_tcp(self, target, message):
        if not self.valid_node(target):
            return "ERROR|INVALID_NODE"

        try:
            with socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            ) as client:

                client.settimeout(CONNECT_TIMEOUT)

                client.connect(
                    (HOST, self.port_for(target))
                )

                client.sendall(
                    (message + "\n").encode()
                )

                client.settimeout(READ_TIMEOUT)

                response = client.makefile("r").readline()

                if not response:
                    return "ERROR|NO_RESPONSE"

                return response.strip()

        except OSError as error:
            return f"ERROR|{error}"

    # --------------------------------------------------
    # MESSAGE HANDLING
    # --------------------------------------------------

    def receive(self, message):
        parts = message.split("|")

        try:
            command = parts[0]

            if command == "TREE":
                if len(parts) != 4:
                    return "ERROR|BAD_TREE"

                return self.receive_tree(
                    int(parts[1]),
                    int(parts[2]),
                    parts[3]
                )

            elif command == "WORK":
                if len(parts) != 4:
                    return "ERROR|BAD_WORK"

                return self.receive_work(
                    int(parts[1]),
                    int(parts[2]),
                    float(parts[3])
                )

            elif command == "RETURN":
                if len(parts) != 4:
                    return "ERROR|BAD_RETURN"

                return self.receive_return(
                    int(parts[1]),
                    int(parts[2]),
                    float(parts[3])
                )

            elif command == "RESET":
                if len(parts) != 4:
                    return "ERROR|BAD_RESET"

                return self.receive_reset(
                    int(parts[1])
                )

            elif command == "ACK":
                if len(parts) != 4:
                    return "ERROR|BAD_ACK"

                self.receive_reset_ack(
                    int(parts[1]),
                    int(parts[2])
                )

                return "ACK"

            return "ERROR|UNKNOWN_MESSAGE"

        except (ValueError, IndexError):
            return "ERROR|BAD_NUMBER"

    # --------------------------------------------------
    # TREE CONFIGURATION
    # --------------------------------------------------

    def receive_tree(self, version, new_parent, child_list):
        with self.lock:

            if self.id == 0:
                return "ERROR|ROOT_CONFIG"

            if self.started and not self.terminated:
                return "ERROR|COMPUTATION_RUNNING"

            if version <= self.tree_version:
                return "ACK"

            if (
                new_parent < -1
                or new_parent >= self.total_nodes
                or new_parent == self.id
            ):
                return "ERROR|BAD_PARENT"

            new_children = set()

            if child_list and child_list != "-":
                for item in child_list.split(","):
                    child = int(item)

                    if (
                        not self.valid_node(child)
                        or child == self.id
                        or child in new_children
                    ):
                        return "ERROR|BAD_CHILD"

                    new_children.add(child)

            self.parent = new_parent
            self.children = new_children
            self.tree_version = version

            print(
                f"Tree configuration updated | "
                f"parent={self.parent} | "
                f"children={self.children}"
            )

            return "ACK"

    # --------------------------------------------------
    # WORK / CREDIT RECEIVING
    # --------------------------------------------------

    def receive_work(self, message_round, sender, amount):
        with self.lock:

            if (
                self.id == 0
                or message_round != self.round
                or self.resetting
                or self.terminated
            ):
                return "ERROR|WORK_NOT_ACCEPTED"

            if sender != self.parent:
                return "ERROR|SENDER_NOT_PARENT"

            if amount < 0:
                return "ERROR|BAD_CREDIT"

            self.weight += amount
            self.active = True

            print(
                f"\nNode {self.id} received "
                f"{amount} credit from parent {sender}"
            )

            print(
                f"Current weight: {self.weight} | "
                f"State: ACTIVE"
            )

            return "ACK"

    def receive_return(self, message_round, sender, amount):
        with self.lock:

            if (
                message_round != self.round
                or self.resetting
                or not self.valid_node(sender)
            ):
                return "ERROR|RETURN_NOT_ACCEPTED"

            if amount < 0:
                return "ERROR|BAD_CREDIT"

            # Root receives returned credit
            if self.id == 0:

                if sender not in self.outstanding_children:
                    return "ERROR|NO_OUTSTANDING_WORK"

                self.controller_weight += amount
                self.outstanding_children.remove(sender)

                print(
                    f"\nRoot received {amount} credit "
                    f"back from child {sender}"
                )

                print(
                    f"Root weight: "
                    f"{self.controller_weight}"
                )

                self.check_termination()

                return "ACK"

            # Worker receives credit from a child
            if (
                sender not in self.children
                or sender not in self.outstanding_children
            ):
                return "ERROR|NOT_AN_OUTSTANDING_CHILD"

            self.weight += amount
            self.outstanding_children.remove(sender)

            print(
                f"\nNode {self.id} received "
                f"{amount} returned credit "
                f"from child {sender}"
            )

            print(
                f"Current weight: {self.weight} | "
                f"Outstanding children: "
                f"{self.outstanding_children}"
            )

            self.try_return_to_parent()

            return "ACK"

    # --------------------------------------------------
    # RESET ACKNOWLEDGEMENT
    # --------------------------------------------------

    def receive_reset(self, new_round):
        with self.lock:

            if self.id == 0 or new_round <= self.round:
                return "ERROR|BAD_RESET_ROUND"

            self.round = new_round
            self.weight = 0.0
            self.active = False
            self.outstanding_children.clear()

            response = self.send_tcp(
                0,
                f"ACK|{self.round}|{self.id}|0"
            )

            return (
                "ACK"
                if response == "ACK"
                else "ERROR|ACK_FAILED"
            )

    def receive_reset_ack(self, ack_round, sender):
        with self.lock:

            if (
                self.id != 0
                or not self.resetting
                or ack_round != self.round
                or not self.valid_node(sender)
                or sender == 0
            ):
                return

            self.reset_ack_nodes.add(sender)

            print(
                f"Reset acknowledgement from Node {sender} "
                f"({len(self.reset_ack_nodes)}/"
                f"{self.total_nodes - 1})"
            )

            if len(self.reset_ack_nodes) == self.total_nodes - 1:
                self.resetting = False

                print(
                    f"\nALL NODES RESET. "
                    f"Round {self.round} is ready."
                )

    # --------------------------------------------------
    # RUNTIME TREE CREATION
    # --------------------------------------------------

    def add_edge(self, parent_node, child_node):
        with self.lock:

            if self.id != 0:
                print("Only Node 0 can create the tree.")
                return

            if self.started and not self.terminated:
                print(
                    "Finish the current computation "
                    "before changing the tree."
                )
                return

            if (
                not self.valid_node(parent_node)
                or not self.valid_node(child_node)
                or parent_node == child_node
            ):
                print("Invalid node IDs.")
                return

            if child_node == 0 or self.parent_of[child_node] != -1:
                print(
                    f"Node {child_node} already has "
                    f"a parent (or is the root)."
                )
                return

            if (
                parent_node != 0
                and self.parent_of[parent_node] == -1
            ):
                print(
                    f"Parent Node {parent_node} "
                    f"is not connected to the root yet."
                )
                return

            self.parent_of[child_node] = parent_node

            self.children_of[parent_node].add(child_node)

            self.root_tree_version += 1

            print(
                f"Added edge: "
                f"{parent_node} -> {child_node}"
            )

            self.broadcast_tree()

    def broadcast_tree(self):
        if self.id != 0:
            return

        for node in range(1, self.total_nodes):

            child_csv = self.join(
                self.children_of[node]
            )

            message = (
                f"TREE|{self.root_tree_version}|"
                f"{self.parent_of[node]}|"
                f"{child_csv}"
            )

            response = self.send_tcp(node, message)

            if response != "ACK":
                print(
                    f"Could not configure Node {node}: "
                    f"{response}. Start it, then use 'sync'."
                )

        self.parent = -1
        self.children = set(self.children_of[0])
        self.tree_version = self.root_tree_version

    @staticmethod
    def join(values):
        if not values:
            return "-"

        return ",".join(
            str(value) for value in sorted(values)
        )

    def print_tree(self):
        if self.id != 0:
            print(
                "Only Node 0 stores and displays "
                "the complete tree."
            )
            return

        print("\n========== RUNTIME TREE ==========")

        self.print_subtree(0, "", True)

        print("==================================")

    def print_subtree(self, node, prefix, last):
        if node == 0:
            print(prefix + "ROOT Node 0")
        else:
            connector = "└── " if last else "├── "
            print(prefix + connector + f"Node {node}")

        children = sorted(self.children_of[node])

        for index, child in enumerate(children):

            child_prefix = prefix

            if node != 0:
                child_prefix += (
                    "    " if last else "│   "
                )

            self.print_subtree(
                child,
                child_prefix,
                index == len(children) - 1
            )

    # --------------------------------------------------
    # COMPUTATION
    # --------------------------------------------------

    def start_work(self, target):
        with self.lock:

            if self.id != 0:
                print(
                    "Only Node 0 starts the computation."
                )
                return

            if self.resetting or self.terminated:
                print(
                    "Cannot start now. "
                    "Check reset/termination status."
                )
                return

            if target not in self.children:
                print(
                    f"Node {target} is not a direct "
                    f"child of Node 0."
                )
                return

            if target in self.outstanding_children:
                print(
                    f"Node {target} already has "
                    f"outstanding work."
                )
                return

            if self.controller_weight <= EPSILON:
                print("Root has no credit available.")
                return

            amount = self.controller_weight / 2.0

            self.controller_weight -= amount
            self.outstanding_children.add(target)
            self.started = True

            response = self.send_tcp(
                target,
                f"WORK|{self.round}|0|{amount}"
            )

            if response != "ACK":
                self.controller_weight += amount
                self.outstanding_children.remove(target)

                print(
                    f"Work transfer failed: {response}. "
                    f"Credit restored."
                )
                return

            print(
                f"Root sent {amount} credit "
                f"to child {target}"
            )

    def send_work(self, target):
        with self.lock:

            if self.id == 0:
                print("Use 'start <child>' on Node 0.")
                return

            if not self.active:
                print("Node is PASSIVE.")
                return

            if target not in self.children:
                print(
                    f"Node {target} is not a direct "
                    f"child of Node {self.id}."
                )
                return

            if target in self.outstanding_children:
                print(
                    f"Node {target} already has "
                    f"outstanding work."
                )
                return

            if self.weight <= EPSILON:
                print("No credit available.")
                return

            amount = self.weight / 2.0

            self.weight -= amount
            self.outstanding_children.add(target)

            response = self.send_tcp(
                target,
                f"WORK|{self.round}|{self.id}|{amount}"
            )

            if response != "ACK":
                self.weight += amount
                self.outstanding_children.remove(target)

                print(
                    f"Work transfer failed: {response}. "
                    f"Credit restored."
                )
                return

            print(
                f"Node {self.id} sent {amount} "
                f"credit to direct child {target}"
            )

    def become_passive(self):
        with self.lock:

            if self.id == 0:
                print(
                    "Node 0 is the controller."
                )
                return

            if not self.active:
                print("Node is already PASSIVE.")
                return

            self.active = False

            print(
                f"Node {self.id} became PASSIVE."
            )

            if not self.outstanding_children:
                self.try_return_to_parent()
            else:
                print(
                    "Waiting for child credit from: "
                    f"{self.outstanding_children}"
                )

    def try_return_to_parent(self):
        if (
            self.id == 0
            or self.active
            or self.outstanding_children
        ):
            return

        if self.parent < 0:
            print(
                "ERROR: worker has no parent "
                "in the configured tree."
            )
            return

        amount = self.weight
        self.weight = 0.0

        response = self.send_tcp(
            self.parent,
            f"RETURN|{self.round}|{self.id}|{amount}"
        )

        if response == "ACK":
            print(
                f"Node {self.id} returned {amount} "
                f"credit to parent {self.parent}."
            )
        else:
            self.weight = amount

            print(
                f"Could not return credit to parent "
                f"{self.parent}: {response}. "
                f"Credit retained."
            )

    def check_termination(self):
        if (
            self.id != 0
            or not self.started
            or self.terminated
            or self.resetting
        ):
            return

        if (
            abs(self.controller_weight - 1.0) <= EPSILON
            and not self.outstanding_children
        ):
            self.terminated = True

            print("\n========================================")
            print("GLOBAL TERMINATION DETECTED")
            print("All computation credit returned to Node 0.")
            print(f"Total credit: {self.controller_weight}")
            print(f"Round {self.round} completed.")
            print("========================================")

            print("Use 'reset' to run another computation.")

    # --------------------------------------------------
    # RESET
    # --------------------------------------------------

    def reset_all(self):
        with self.lock:

            if self.id != 0:
                print("Only Node 0 can reset.")
                return

            if not self.terminated:
                print(
                    "Reset is allowed only "
                    "after global termination."
                )
                return

            self.round += 1
            self.controller_weight = 1.0

            self.started = False
            self.terminated = False
            self.resetting = True

            self.outstanding_children.clear()
            self.reset_ack_nodes.clear()

            print(
                f"Starting reset for round {self.round}..."
            )

            for node in range(1, self.total_nodes):

                response = self.send_tcp(
                    node,
                    f"RESET|{self.round}|0|0"
                )

                if response != "ACK":
                    print(
                        f"Reset request to Node {node} "
                        f"failed: {response}"
                    )

            if self.total_nodes == 1:
                self.resetting = False

                print(
                    "Reset complete. "
                    "Ready for another round."
                )
            else:
                print(
                    "Waiting for reset acknowledgements: "
                    f"{self.total_nodes - 1} workers."
                )

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def show_status(self):
        with self.lock:

            print(
                f"\n========== NODE {self.id} STATUS =========="
            )

            print(f"Port       : {self.port}")
            print(f"Round      : {self.round}")

            print(
                f"Parent     : "
                f"{'none (root)' if self.parent == -1 else self.parent}"
            )

            print(f"Children   : {self.children}")

            if self.id == 0:

                print(
                    f"Root weight: {self.controller_weight}"
                )

                print(f"Started    : {self.started}")
                print(f"Terminated : {self.terminated}")
                print(f"Resetting  : {self.resetting}")

            else:

                print(f"Weight     : {self.weight}")

                print(
                    f"State      : "
                    f"{'ACTIVE' if self.active else 'PASSIVE'}"
                )

            print(
                f"Outstanding: {self.outstanding_children}"
            )

            print("====================================\n")

    # --------------------------------------------------
    # COMMAND LINE INTERFACE
    # --------------------------------------------------

    def print_help(self):
        if self.id == 0:

            print("\nRoot commands:")
            print("  add <parent> <child>")
            print("  tree")
            print("  sync")
            print("  start <child>")
            print("  reset")
            print("  status")
            print("  help")
            print("  exit")

        else:

            print("\nWorker commands:")
            print("  send <child>")
            print("  passive")
            print("  status")
            print("  help")
            print("  exit")

    def command_loop(self):
        self.start_server()

        time.sleep(0.4)

        print(
            f"\nStarted Node {self.id} | "
            f"port={self.port} | "
            f"totalNodes={self.total_nodes}"
        )

        if self.id == 0:
            print(
                "Node 0 is the root. "
                "Create the tree using 'add <parent> <child>'."
            )
        else:
            print(
                "Waiting for tree configuration "
                "from Node 0..."
            )

        self.print_help()

        while self.running:

            try:
                line = input(
                    f"Node {self.id}> "
                ).strip()

            except EOFError:
                break

            if not line:
                continue

            parts = line.split()
            command = parts[0].lower()

            try:

                if command == "add":

                    if len(parts) != 3:
                        print("Usage: add <parent> <child>")
                    else:
                        self.add_edge(
                            int(parts[1]),
                            int(parts[2])
                        )

                elif command == "tree":
                    self.print_tree()

                elif command == "sync":

                    if self.id == 0:
                        self.broadcast_tree()
                    else:
                        print(
                            "Only Node 0 can synchronize."
                        )

                elif command == "start":

                    if len(parts) != 2:
                        print("Usage: start <child>")
                    else:
                        self.start_work(
                            int(parts[1])
                        )

                elif command == "send":

                    if len(parts) != 2:
                        print("Usage: send <child>")
                    else:
                        self.send_work(
                            int(parts[1])
                        )

                elif command == "passive":
                    self.become_passive()

                elif command == "reset":
                    self.reset_all()

                elif command == "status":
                    self.show_status()

                elif command == "help":
                    self.print_help()

                elif command == "exit":

                    if (
                        self.id == 0
                        and self.started
                        and not self.terminated
                    ):
                        print(
                            "Cannot exit during "
                            "an active computation."
                        )

                    elif (
                        self.id != 0
                        and (
                            self.active
                            or self.outstanding_children
                        )
                    ):
                        print(
                            "Cannot exit while active "
                            "or waiting for child credit."
                        )

                    else:
                        self.running = False

                        print(
                            f"Node {self.id} exiting."
                        )

                        break

                else:
                    print(
                        "Unknown command. Type 'help'."
                    )

            except ValueError:
                print("Invalid numeric argument.")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    if len(sys.argv) != 3:

        print(
            "Usage: python huang.py <nodeId> <totalNodes>"
        )

        print(
            "Example: python huang.py 0 5"
        )

        return

    try:
        node_id = int(sys.argv[1])
        total_nodes = int(sys.argv[2])

        if not 1 <= total_nodes <= 100:
            raise ValueError(
                "totalNodes must be 1..100"
            )

        if not 0 <= node_id < total_nodes:
            raise ValueError(
                f"nodeId must be between "
                f"0 and {total_nodes - 1}"
            )

        if BASE_PORT + total_nodes - 1 > 65535:
            raise ValueError(
                "Port range exceeds 65535"
            )

        node = Huang(node_id, total_nodes)

        node.command_loop()

    except Exception as error:
        print(
            f"Startup/runtime error: {error}"
        )


if __name__ == "__main__":
    main()
