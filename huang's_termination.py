
from fractions import Fraction


class Process:

    def __init__(self, pid, is_controller=False):
        self.pid = pid
        self.is_controller = is_controller

        # Controller starts with weight 1
        # Worker processes start with weight 0
        self.weight = Fraction(1) if is_controller else Fraction(0)

        # Controller initially active; workers passive
        self.active = is_controller

        self.sent_messages = 0
        self.received_messages = 0

    def state(self):
        return "ACTIVE" if self.active else "PASSIVE"


class HuangTerminationSimulator:

    def __init__(self, number_of_workers):

        # Controller is P0
        self.controller = Process(0, is_controller=True)

        # Workers are P1, P2, ...
        self.workers = {
            i: Process(i)
            for i in range(1, number_of_workers + 1)
        }

        # Computation messages B(weight)
        self.computation_messages = []

        # Control messages C(weight)
        self.control_messages = []

        self.message_id = 1
        self.terminated = False

    # ----------------------------------------
    # Get process by ID
    # ----------------------------------------

    def get_process(self, pid):

        if pid == 0:
            return self.controller

        return self.workers.get(pid)

    # ----------------------------------------
    # Send computation message B(weight)
    # ----------------------------------------

    def send_computation_message(self, sender_id, receiver_id, fraction):

        sender = self.get_process(sender_id)
        receiver = self.get_process(receiver_id)

        if sender is None or receiver is None:
            print("Invalid process ID.")
            return

        # Controller or active worker can send work
        if not sender.active:
            print(f"P{sender_id} is passive and cannot send work.")
            return

        # Receiver must be a worker
        if receiver_id == 0:
            print("The controller cannot receive computation work.")
            return

        if sender_id == receiver_id:
            print("A process cannot send work to itself.")
            return

        if fraction <= 0 or fraction >= 1:
            print("Fraction must be between 0 and 1.")
            return

        # Split sender's weight
        sent_weight = sender.weight * fraction
        remaining_weight = sender.weight - sent_weight

        if sent_weight <= 0 or remaining_weight <= 0:
            print("Invalid weight split.")
            return

        sender.weight = remaining_weight
        sender.sent_messages += 1

        message = {
            "id": self.message_id,
            "sender": sender_id,
            "receiver": receiver_id,
            "weight": sent_weight
        }

        self.computation_messages.append(message)

        print("\nComputation message created: B(weight)")
        print(f"Message ID: B{self.message_id}")
        print(f"Sender: P{sender_id}")
        print(f"Receiver: P{receiver_id}")
        print(f"Weight sent: {sent_weight}")
        print(f"Weight retained by P{sender_id}: {sender.weight}")

        self.message_id += 1

        self.check_termination()

    # ----------------------------------------
    # Deliver computation message
    # ----------------------------------------

    def deliver_computation_message(self, message_id):

        message = None

        for msg in self.computation_messages:
            if msg["id"] == message_id:
                message = msg
                break

        if message is None:
            print("Computation message not found.")
            return

        receiver = self.workers[message["receiver"]]

        # Receiver collects message weight
        receiver.weight += message["weight"]
        receiver.received_messages += 1

        # Passive receiver becomes active
        if not receiver.active:
            receiver.active = True

        self.computation_messages.remove(message)

        print(f"\nB{message_id} delivered to P{receiver.pid}")
        print(f"Weight received: {message['weight']}")
        print(f"New weight of P{receiver.pid}: {receiver.weight}")
        print(f"State of P{receiver.pid}: {receiver.state()}")

        self.check_termination()

    # ----------------------------------------
    # Process becomes passive
    # ----------------------------------------

    def become_passive(self, pid):

        process = self.get_process(pid)

        if process is None:
            print("Invalid process ID.")
            return

        if not process.active:
            print(f"P{pid} is already passive.")
            return

        # Controller becomes passive but retains its weight
        if process.is_controller:

            process.active = False

            print("\nController P0 becomes PASSIVE.")
            print(f"Controller weight: {process.weight}")

            self.check_termination()
            return

        # Worker returns all its weight to controller
        returned_weight = process.weight

        if returned_weight > 0:

            control_message = {
                "id": self.message_id,
                "sender": pid,
                "receiver": 0,
                "weight": returned_weight
            }

            self.control_messages.append(control_message)

            print(f"\nP{pid} becomes PASSIVE.")
            print(f"P{pid} sends control message C({returned_weight})")
            print(f"Control message ID: C{self.message_id}")

            self.message_id += 1

        else:

            print(f"\nP{pid} becomes PASSIVE with zero weight.")

        # Worker gives up its weight
        process.weight = Fraction(0)
        process.active = False

        self.check_termination()

    # ----------------------------------------
    # Deliver control message C(weight)
    # ----------------------------------------

    def deliver_control_message(self, message_id):

        message = None

        for msg in self.control_messages:
            if msg["id"] == message_id:
                message = msg
                break

        if message is None:
            print("Control message not found.")
            return

        # Controller collects returned weight
        self.controller.weight += message["weight"]

        self.control_messages.remove(message)

        print(f"\nC{message_id} delivered to controller P0")
        print(f"Weight returned: {message['weight']}")
        print(f"Controller's new weight: {self.controller.weight}")

        self.check_termination()

    # ----------------------------------------
    # Display computation messages
    # ----------------------------------------

    def display_computation_messages(self):

        print("\n===== COMPUTATION MESSAGES IN TRANSIT =====")

        if not self.computation_messages:
            print("No computation messages in transit.")

        for msg in self.computation_messages:

            print(
                f"B{msg['id']}: P{msg['sender']} -> "
                f"P{msg['receiver']} | Weight: {msg['weight']}"
            )

    # ----------------------------------------
    # Display control messages
    # ----------------------------------------

    def display_control_messages(self):

        print("\n======= CONTROL MESSAGES IN TRANSIT =======")

        if not self.control_messages:
            print("No control messages in transit.")

        for msg in self.control_messages:

            print(
                f"C{msg['id']}: P{msg['sender']} -> P0 | "
                f"Weight: {msg['weight']}"
            )

    # ----------------------------------------
    # Display process status
    # ----------------------------------------

    def display_status(self):

        print("\n========== PROCESS STATUS ==========")

        print(
            f"P0 (Controller): {self.controller.state()}, "
            f"Weight = {self.controller.weight}"
        )

        for pid, process in self.workers.items():

            print(
                f"P{pid}: {process.state()}, "
                f"Weight = {process.weight}"
            )

        print("===================================")

    # ----------------------------------------
    # Check weight conservation
    # ----------------------------------------

    def total_weight(self):

        total = self.controller.weight

        for process in self.workers.values():
            total += process.weight

        for msg in self.computation_messages:
            total += msg["weight"]

        for msg in self.control_messages:
            total += msg["weight"]

        return total

    # ----------------------------------------
    # Termination detection
    # ----------------------------------------

    def check_termination(self):

        total = self.total_weight()

        print(f"\nTotal weight in system: {total}")

        if total != 1:
            print("WARNING: Weight conservation violated!")
            return

        # Huang termination condition:
        # Controller is passive and recovered weight 1
        if (
            not self.controller.active
            and self.controller.weight == 1
            and not self.computation_messages
            and not self.control_messages
        ):

            if not self.terminated:

                self.terminated = True

                print("\n" + "=" * 50)
                print("DISTRIBUTED COMPUTATION TERMINATED!")
                print("Controller has recovered total weight 1.")
                print("=" * 50)

        else:

            print("Termination not detected yet.")

    # ----------------------------------------
    # Display full weight distribution
    # ----------------------------------------

    def display_weight_distribution(self):

        print("\n========== WEIGHT DISTRIBUTION ==========")

        print(f"Controller P0: {self.controller.weight}")

        for pid, process in self.workers.items():
            print(f"P{pid}: {process.weight}")

        print("\nComputation message weights:")

        for msg in self.computation_messages:
            print(f"B{msg['id']}: {msg['weight']}")

        print("\nControl message weights:")

        for msg in self.control_messages:
            print(f"C{msg['id']}: {msg['weight']}")

        print(f"\nTotal weight: {self.total_weight()}")
        print("========================================")


# ==========================================
# DYNAMIC SIMULATOR
# ==========================================

print("=" * 55)
print(" HUANG'S TERMINATION DETECTION SIMULATOR")
print("=" * 55)

while True:

    try:
        n = int(input("\nEnter number of worker processes: "))

        if n > 0:
            break

        print("Enter a positive number.")

    except ValueError:
        print("Enter a valid integer.")


simulator = HuangTerminationSimulator(n)


# ==========================================
# MAIN MENU
# ==========================================

while True:

    print("\n=============== MENU ===============")

    print("1. Send Computation Message B(weight)")
    print("2. Deliver Computation Message")
    print("3. Process Becomes Passive")
    print("4. Deliver Control Message C(weight)")
    print("5. Display Process Status")
    print("6. Display Computation Messages")
    print("7. Display Control Messages")
    print("8. Display Weight Distribution")
    print("9. Exit")

    choice = input("\nEnter choice: ").strip()


    # --------------------------------------
    # 1. SEND COMPUTATION MESSAGE
    # --------------------------------------

    if choice == "1":

        try:

            sender = int(input("Enter sender process (0 = controller): "))
            receiver = int(input("Enter receiver worker process: "))

            fraction_text = input(
                "Enter fraction of sender's weight to send (e.g. 1/2): "
            )

            fraction = Fraction(fraction_text)

        except (ValueError, ZeroDivisionError):

            print("Invalid input.")
            continue

        simulator.send_computation_message(
            sender,
            receiver,
            fraction
        )


    # --------------------------------------
    # 2. DELIVER COMPUTATION MESSAGE
    # --------------------------------------

    elif choice == "2":

        simulator.display_computation_messages()

        try:
            message_id = int(input("Enter B message ID to deliver: "))
        except ValueError:
            print("Invalid message ID.")
            continue

        simulator.deliver_computation_message(message_id)


    # --------------------------------------
    # 3. PROCESS BECOMES PASSIVE
    # --------------------------------------

    elif choice == "3":

        try:
            pid = int(input("Enter process ID (0 = controller): "))
        except ValueError:
            print("Invalid process ID.")
            continue

        simulator.become_passive(pid)


    # --------------------------------------
    # 4. DELIVER CONTROL MESSAGE
    # --------------------------------------

    elif choice == "4":

        simulator.display_control_messages()

        try:
            message_id = int(input("Enter C message ID to deliver: "))
        except ValueError:
            print("Invalid message ID.")
            continue

        simulator.deliver_control_message(message_id)


    # --------------------------------------
    # 5. DISPLAY STATUS
    # --------------------------------------

    elif choice == "5":

        simulator.display_status()


    # --------------------------------------
    # 6. DISPLAY COMPUTATION MESSAGES
    # --------------------------------------

    elif choice == "6":

        simulator.display_computation_messages()


    # --------------------------------------
    # 7. DISPLAY CONTROL MESSAGES
    # --------------------------------------

    elif choice == "7":

        simulator.display_control_messages()


    # --------------------------------------
    # 8. DISPLAY WEIGHT DISTRIBUTION
    # --------------------------------------

    elif choice == "8":

        simulator.display_weight_distribution()


    # --------------------------------------
    # 9. EXIT
    # --------------------------------------

    elif choice == "9":

        print("\nExiting Huang's Termination Detection Simulator.")
        simulator.display_status()
        simulator.display_weight_distribution()

        break


    else:

        print("Invalid choice. Select 1-9.")
