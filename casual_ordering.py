
class Process:

    def __init__(self, pid, total_processes):
        self.pid = pid
        self.clock = [0] * total_processes

        # Messages received but not yet deliverable
        self.pending = []

        # Messages successfully delivered
        self.delivered = []

    # --------------------------------
    # BROADCAST MESSAGE
    # --------------------------------

    def broadcast(self, text, message_id):

        # Increment sender's own clock
        self.clock[self.pid] += 1

        msg = {
            "id": message_id,
            "text": text,
            "sender": self.pid,
            "clock": self.clock.copy()
        }

        print(f"\nP{self.pid + 1} BROADCASTS M{message_id}")
        print("Message:", text)
        print("Timestamp:", self.clock)

        # Sender delivers its own broadcast locally
        self.delivered.append(msg.copy())

        print(f"P{self.pid + 1} DELIVERS M{message_id} locally.")

        return msg

    # --------------------------------
    # RECEIVE MESSAGE
    # --------------------------------

    def receive_message(self, msg):

        print(
            f"\nP{self.pid + 1} receives M{msg['id']} "
            f"from P{msg['sender'] + 1}"
        )

        print("Message:", msg["text"])

        # Store received message
        self.pending.append(msg.copy())

        # Check causal delivery
        self.check_pending_messages()

    # --------------------------------
    # CHECK CAUSAL DELIVERY CONDITION
    # --------------------------------

    def can_deliver(self, msg):

        sender = msg["sender"]
        timestamp = msg["clock"]

        # Condition 1:
        # Previous messages from the same sender
        if timestamp[sender] != self.clock[sender] + 1:
            return False

        # Condition 2:
        # All causally preceding messages must be delivered
        for i in range(len(self.clock)):

            if i != sender:

                if timestamp[i] > self.clock[i]:
                    return False

        return True

    # --------------------------------
    # DELIVER MESSAGE
    # --------------------------------

    def deliver_message(self, msg):

        timestamp = msg["clock"]

        # Update vector clock
        for i in range(len(self.clock)):
            self.clock[i] = max(
                self.clock[i],
                timestamp[i]
            )

        self.delivered.append(msg.copy())

        print(
            f"\nP{self.pid + 1} DELIVERS M{msg['id']}: "
            f"{msg['text']}"
        )

        print("Updated vector clock:", self.clock)

    # --------------------------------
    # CHECK PENDING MESSAGES
    # --------------------------------

    def check_pending_messages(self):

        progress = True

        while progress:

            progress = False

            for msg in self.pending.copy():

                if self.can_deliver(msg):

                    self.deliver_message(msg)

                    self.pending.remove(msg)

                    progress = True

                    break


# ==========================================
# DYNAMIC CAUSAL ORDERING SIMULATOR
# ==========================================

print("========================================")
print(" CAUSAL ORDERING USING VECTOR CLOCKS")
print("========================================")


# Get number of processes
while True:

    try:
        n = int(input("\nEnter number of processes: "))

        if n > 0:
            break

        print("Enter a positive number.")

    except ValueError:
        print("Enter a valid integer.")


# Create processes dynamically
processes = {}

for i in range(n):
    processes[i + 1] = Process(i, n)


# Store individual broadcast copies waiting in network
network_messages = []

message_id = 1


# ==========================================
# SELECT PROCESS
# ==========================================

def select_process(prompt):

    while True:

        try:
            pid = int(input(prompt))

            if pid in processes:
                return pid

            print(f"Choose a process between 1 and {n}.")

        except ValueError:
            print("Enter a valid process number.")


# ==========================================
# DISPLAY ALL VECTOR CLOCKS
# ==========================================

def display_clocks():

    print("\n========== VECTOR CLOCKS ==========")

    for pid, process in processes.items():

        print(f"P{pid}: {process.clock}")

    print("===================================")


# ==========================================
# DISPLAY MESSAGES IN NETWORK
# ==========================================

def display_network():

    print("\n========== MESSAGES IN TRANSIT ==========")

    if not network_messages:

        print("No messages in transit.")

    else:

        for msg in network_messages:

            print(
                f"M{msg['id']} -> P{msg['receiver']} | "
                f"From P{msg['sender'] + 1} | "
                f"Message: {msg['text']} | "
                f"Clock: {msg['clock']}"
            )

    print("=========================================")


# ==========================================
# DISPLAY PENDING MESSAGES
# ==========================================

def display_pending():

    print("\n========== CAUSALLY PENDING MESSAGES ==========")

    found = False

    for pid, process in processes.items():

        for msg in process.pending:

            found = True

            print(
                f"M{msg['id']} at P{pid} | "
                f"From P{msg['sender'] + 1} | "
                f"Message: {msg['text']} | "
                f"Clock: {msg['clock']}"
            )

    if not found:
        print("No causally pending messages.")

    print("================================================")


# ==========================================
# DISPLAY DELIVERED MESSAGES
# ==========================================

def display_delivered():

    print("\n========== DELIVERED MESSAGES ==========")

    for pid, process in processes.items():

        print(f"\nProcess P{pid}:")

        if not process.delivered:

            print("No messages delivered.")

        else:

            for msg in process.delivered:

                print(
                    f"M{msg['id']}: {msg['text']} "
                    f"(from P{msg['sender'] + 1})"
                )

    print("========================================")


# ==========================================
# MAIN MENU
# ==========================================

while True:

    print("\n============== MAIN MENU ==============")

    print("1. Broadcast Message")
    print("2. Deliver Message to a Receiver")
    print("3. Display All Vector Clocks")
    print("4. Display Messages in Transit")
    print("5. Display Causally Pending Messages")
    print("6. Display Delivered Messages")
    print("7. Display Individual Process Status")
    print("8. Exit")

    choice = input("\nEnter your choice: ").strip()


    # --------------------------------------
    # 1. BROADCAST MESSAGE
    # --------------------------------------

    if choice == "1":

        sender = select_process("Enter sender process: ")

        text = input("Enter message: ").strip()

        if not text:

            print("Message cannot be empty.")
            continue

        # Sender broadcasts message
        msg = processes[sender].broadcast(
            text,
            message_id
        )

        # Create one copy for every other process
        for receiver in processes:

            if receiver != sender:

                network_messages.append({
                    **msg,
                    "receiver": receiver
                })

        print(
            f"\nM{message_id} broadcast to "
            f"all {n - 1} other processes."
        )

        message_id += 1


    # --------------------------------------
    # 2. DELIVER MESSAGE TO RECEIVER
    # --------------------------------------

    elif choice == "2":

        if not network_messages:

            print("\nNo messages are waiting in the network.")
            continue

        display_network()

        try:

            selected_id = int(
                input("\nEnter message ID to deliver: ")
            )

            receiver = int(
                input("Enter receiver process: ")
            )

        except ValueError:

            print("Enter valid numbers.")
            continue

        if receiver not in processes:

            print("Invalid receiver.")
            continue

        selected_msg = None

        # Find the exact message copy
        for msg in network_messages:

            if (
                msg["id"] == selected_id
                and msg["receiver"] == receiver
            ):

                selected_msg = msg
                break

        if selected_msg is None:

            print("Message copy not found.")
            continue

        # Remove from network
        network_messages.remove(selected_msg)

        # Send copy to receiver
        processes[receiver].receive_message(selected_msg)

        print("\nReceiver's causal delivery check completed.")


    # --------------------------------------
    # 3. DISPLAY ALL CLOCKS
    # --------------------------------------

    elif choice == "3":

        display_clocks()


    # --------------------------------------
    # 4. DISPLAY NETWORK MESSAGES
    # --------------------------------------

    elif choice == "4":

        display_network()


    # --------------------------------------
    # 5. DISPLAY PENDING MESSAGES
    # --------------------------------------

    elif choice == "5":

        display_pending()


    # --------------------------------------
    # 6. DISPLAY DELIVERED MESSAGES
    # --------------------------------------

    elif choice == "6":

        display_delivered()


    # --------------------------------------
    # 7. INDIVIDUAL PROCESS STATUS
    # --------------------------------------

    elif choice == "7":

        pid = select_process("Enter process number: ")

        process = processes[pid]

        print(f"\n========== P{pid} STATUS ==========")

        print("Vector Clock:", process.clock)

        print("\nDelivered Messages:")

        for msg in process.delivered:
            print(f"M{msg['id']}: {msg['text']}")

        print("\nPending Messages:")

        if process.pending:

            for msg in process.pending:
                print(f"M{msg['id']}: {msg['text']}")

        else:

            print("None")

        print("===================================")


    # --------------------------------------
    # 8. EXIT
    # --------------------------------------

    elif choice == "8":

        print("\nExiting Causal Ordering Simulator.")

        display_clocks()
        display_delivered()

        break


    else:

        print("Invalid choice. Select 1-8.")
