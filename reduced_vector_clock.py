
class SparseVectorClock:

    def __init__(self, process_id):
        self.process_id = process_id
        self.clock = {}

    # Get clock value; missing entries mean zero
    def get_value(self, process):
        return self.clock.get(process, 0)

    # Increment own clock
    def increment(self):
        self.clock[self.process_id] = (
            self.get_value(self.process_id) + 1
        )

    # Internal event
    def internal_event(self):
        self.increment()
        print(f"\nP{self.process_id + 1} performs internal event.")
        print(f"Updated clock: {self.clock}")

    # Send message
    def send_message(self):
        self.increment()

        message = self.clock.copy()

        print(f"\nP{self.process_id + 1} sends message.")
        print(f"Message timestamp: {message}")

        return message

    # Receive message
    def receive_message(self, received_clock):

        # Merge received clock with local clock
        for process, timestamp in received_clock.items():
            self.clock[process] = max(
                self.get_value(process),
                timestamp
            )

        # Increment receiver's own clock
        self.increment()

        print(f"\nP{self.process_id + 1} receives message.")
        print(f"Updated clock: {self.clock}")


# ----------------------------------
# DYNAMIC DISTRIBUTED SYSTEM
# ----------------------------------

print("===== SPARSE VECTOR CLOCK SIMULATOR =====")

# Get number of processes
while True:
    try:
        n = int(input("\nEnter number of processes: "))

        if n > 0:
            break

        print("Number of processes must be positive.")

    except ValueError:
        print("Please enter a valid integer.")


# Create processes dynamically
processes = {}

for i in range(n):
    processes[i + 1] = SparseVectorClock(i)


# Store messages waiting to be delivered
pending_messages = []

message_id = 1


# Validate process selection
def select_process(message):

    while True:
        try:
            pid = int(input(message))

            if pid in processes:
                return pid

            print(f"Please select a process between 1 and {n}.")

        except ValueError:
            print("Enter a valid process number.")


# Display all vector clocks
def display_all_clocks():

    print("\n========== ALL VECTOR CLOCKS ==========")

    for pid, process in processes.items():
        print(f"P{pid}: {process.clock}")

    print("=======================================")


# Main menu
while True:

    print("\n========== MENU ==========")
    print("1. Perform Internal Event")
    print("2. Send Message")
    print("3. Deliver Pending Message")
    print("4. Display All Vector Clocks")
    print("5. Display Individual Process Clock")
    print("6. View Pending Messages")
    print("7. Exit")

    choice = input("\nEnter your choice: ").strip()

    # 1. Internal event
    if choice == "1":

        pid = select_process("Select process for internal event: ")

        processes[pid].internal_event()


    # 2. Send message
    elif choice == "2":

        sender = select_process("Enter sender process: ")
        receiver = select_process("Enter receiver process: ")

        if sender == receiver:
            print("\nA process cannot send a message to itself.")
            continue

        # Generate message timestamp
        timestamp = processes[sender].send_message()

        # Store message for later delivery
        pending_messages.append({
            "id": message_id,
            "sender": sender,
            "receiver": receiver,
            "timestamp": timestamp
        })

        print(f"\nMessage M{message_id} created.")
        print(f"Sender: P{sender}")
        print(f"Receiver: P{receiver}")
        print("Message added to pending queue.")

        message_id += 1


    # 3. Deliver pending message
    elif choice == "3":

        if not pending_messages:
            print("\nNo pending messages to deliver.")
            continue

        print("\n======= PENDING MESSAGES =======")

        for msg in pending_messages:
            print(
                f"M{msg['id']}: "
                f"P{msg['sender']} -> P{msg['receiver']} "
                f"| Timestamp: {msg['timestamp']}"
            )

        try:
            selected_id = int(
                input("\nEnter message ID to deliver: ")
            )
        except ValueError:
            print("Invalid message ID.")
            continue

        selected_message = None

        for msg in pending_messages:
            if msg["id"] == selected_id:
                selected_message = msg
                break

        if selected_message is None:
            print("Message not found.")
            continue

        receiver = selected_message["receiver"]

        # Deliver the message
        processes[receiver].receive_message(
            selected_message["timestamp"]
        )

        # Remove delivered message
        pending_messages.remove(selected_message)

        print(f"Message M{selected_id} delivered successfully.")


    # 4. Display all clocks
    elif choice == "4":

        display_all_clocks()


    # 5. Display individual clock
    elif choice == "5":

        pid = select_process("Enter process number: ")

        print(f"\nP{pid} Vector Clock: {processes[pid].clock}")


    # 6. Display pending messages
    elif choice == "6":

        print("\n======= PENDING MESSAGES =======")

        if not pending_messages:
            print("No pending messages.")
        else:
            for msg in pending_messages:
                print(
                    f"M{msg['id']}: "
                    f"P{msg['sender']} -> P{msg['receiver']} "
                    f"| {msg['timestamp']}"
                )


    # 7. Exit
    elif choice == "7":

        print("\nExiting Sparse Vector Clock Simulator.")
        print("Final Vector Clocks:")
        display_all_clocks()

        break


    else:
        print("\nInvalid choice. Please select 1-7.")
