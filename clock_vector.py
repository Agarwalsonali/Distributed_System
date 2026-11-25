
class VectorClock:
    def __init__(self, process_id, total_processes):
        self.process_id = process_id

        # Normal vector clock:
        # Every process stores one entry for every process.
        self.clock = [0] * total_processes

    def internal_event(self):
        # Increment this process's own clock entry.
        self.clock[self.process_id] += 1

    def send_message(self):
        # Sending a message is also an event.
        self.clock[self.process_id] += 1

        # Attach a copy of the current vector clock.
        return self.clock.copy()

    def receive_message(self, message_clock):
        # Merge the received clock with the local clock.
        for i in range(len(self.clock)):
            self.clock[i] = max(
                self.clock[i],
                message_clock[i]
            )

        # Increment receiver's own clock after merging.
        self.clock[self.process_id] += 1

    def display_clock(self):
        return self.clock


class Message:
    def __init__(self, message_id, sender, receiver, timestamp):
        self.message_id = message_id
        self.sender = sender
        self.receiver = receiver
        self.timestamp = timestamp


def get_process_number(prompt, total_processes):
    while True:
        try:
            number = int(input(prompt))

            if 1 <= number <= total_processes:
                return number - 1

            print(
                f"Please enter a process number "
                f"between 1 and {total_processes}."
            )

        except ValueError:
            print("Please enter a valid integer.")


def main():
    print("===== NORMAL VECTOR CLOCK SIMULATOR =====")

    while True:
        try:
            total_processes = int(
                input("\nEnter number of processes: ")
            )

            if total_processes > 0:
                break

            print("Number of processes must be positive.")

        except ValueError:
            print("Please enter a valid integer.")

    # Create processes dynamically.
    processes = [
        VectorClock(i, total_processes)
        for i in range(total_processes)
    ]

    pending_messages = []
    next_message_id = 1

    while True:
        print("\n========== MENU ==========")
        print("1. Perform Internal Event")
        print("2. Send Message")
        print("3. Deliver Pending Message")
        print("4. Display All Vector Clocks")
        print("5. Display Individual Process Clock")
        print("6. View Pending Messages")
        print("7. Exit")

        choice = input("\nEnter your choice: ")

        # 1. Internal event
        if choice == "1":
            process_id = get_process_number(
                "Select process for internal event: ",
                total_processes
            )

            processes[process_id].internal_event()

            print(
                f"\nP{process_id + 1} performs internal event."
            )
            print(
                "Updated clock:",
                processes[process_id].display_clock()
            )

        # 2. Send message
        elif choice == "2":
            sender = get_process_number(
                "Enter sender process: ",
                total_processes
            )

            receiver = get_process_number(
                "Enter receiver process: ",
                total_processes
            )

            if sender == receiver:
                print("Sender and receiver must be different.")
                continue

            timestamp = processes[sender].send_message()

            message = Message(
                next_message_id,
                sender,
                receiver,
                timestamp
            )

            pending_messages.append(message)

            print(f"\nP{sender + 1} sends message.")
            print("Message timestamp:", timestamp)

            print(f"\nMessage M{next_message_id} created.")
            print(f"Sender: P{sender + 1}")
            print(f"Receiver: P{receiver + 1}")
            print("Message added to pending queue.")

            next_message_id += 1

        # 3. Deliver pending message
        elif choice == "3":
            if not pending_messages:
                print("\nNo pending messages.")
                continue

            print("\n======= PENDING MESSAGES =======")

            for message in pending_messages:
                print(
                    f"M{message.message_id}: "
                    f"P{message.sender + 1} -> "
                    f"P{message.receiver + 1} | "
                    f"Timestamp: {message.timestamp}"
                )

            try:
                message_id = int(
                    input("\nEnter message ID to deliver: ")
                )

            except ValueError:
                print("Invalid message ID.")
                continue

            selected_message = None

            for message in pending_messages:
                if message.message_id == message_id:
                    selected_message = message
                    break

            if selected_message is None:
                print("Message ID not found.")
                continue

            receiver = selected_message.receiver

            processes[receiver].receive_message(
                selected_message.timestamp
            )

            print(f"\nP{receiver + 1} receives message.")
            print(
                "Updated clock:",
                processes[receiver].display_clock()
            )

            print(
                f"Message M{message_id} delivered successfully."
            )

            pending_messages.remove(selected_message)

        # 4. Display all clocks
        elif choice == "4":
            print("\n========== ALL VECTOR CLOCKS ==========")

            for i, process in enumerate(processes):
                print(
                    f"P{i + 1}:",
                    process.display_clock()
                )

            print("======================================")

        # 5. Display individual clock
        elif choice == "5":
            process_id = get_process_number(
                "Enter process number: ",
                total_processes
            )

            print(
                f"\nP{process_id + 1} Vector Clock:",
                processes[process_id].display_clock()
            )

        # 6. View pending messages
        elif choice == "6":
            print("\n======= PENDING MESSAGES =======")

            if not pending_messages:
                print("No pending messages.")

            else:
                for message in pending_messages:
                    print(
                        f"M{message.message_id}: "
                        f"P{message.sender + 1} -> "
                        f"P{message.receiver + 1} | "
                        f"{message.timestamp}"
                    )

        # 7. Exit
        elif choice == "7":
            print("\nExiting Normal Vector Clock Simulator.")
            break

        else:
            print("Invalid choice. Please select 1-7.")


if __name__ == "__main__":
    main()
