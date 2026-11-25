
class Process:

    def __init__(self, process_id):
        self.process_id = process_id
        self.has_token = False
        self.wants_to_enter = False
        self.cs_entries = 0

    # Request critical section
    def request_critical_section(self):

        if self.wants_to_enter:
            print(f"P{self.process_id} already has a pending request.")
        else:
            self.wants_to_enter = True
            print(f"\nP{self.process_id} requests Critical Section.")

            if self.has_token:
                print("P{} already has the token.".format(self.process_id))
                self.enter_critical_section()

            else:
                print("Request is waiting for the token.")

    # Cancel critical section request
    def cancel_request(self):

        if self.wants_to_enter:
            self.wants_to_enter = False
            print(f"\nP{self.process_id} cancels its CS request.")
        else:
            print(f"\nP{self.process_id} has no pending request.")

    # Receive token
    def receive_token(self):

        self.has_token = True

        print(f"\nP{self.process_id} receives the token.")

        if self.wants_to_enter:
            self.enter_critical_section()
        else:
            print(f"P{self.process_id} does not want CS.")
            print("Token will be passed when you choose to continue.")

    # Enter critical section
    def enter_critical_section(self):

        if self.has_token and self.wants_to_enter:

            print("\n" + "=" * 45)
            print(f"P{self.process_id} ENTERS CRITICAL SECTION")
            print("Shared resource is being used...")
            print(f"P{self.process_id} EXITS CRITICAL SECTION")
            print("=" * 45)

            self.cs_entries += 1

            # Request is completed
            self.wants_to_enter = False

    # Display process status
    def display_status(self):

        print(f"\nProcess P{self.process_id}")

        print("Token:", "Yes" if self.has_token else "No")

        print(
            "CS Request:",
            "Pending" if self.wants_to_enter else "No"
        )

        print("Total CS entries:", self.cs_entries)


# ==========================================
# RING-BASED TOKEN MUTUAL EXCLUSION
# ==========================================

print("=" * 50)
print(" RING-BASED TOKEN MUTUAL EXCLUSION SIMULATOR")
print("=" * 50)


# Get number of processes
while True:

    try:
        n = int(input("\nEnter number of processes: "))

        if n > 0:
            break

        print("Number of processes must be positive.")

    except ValueError:
        print("Enter a valid integer.")


# Create processes dynamically
processes = []

for i in range(n):
    processes.append(Process(i + 1))


# Initially token is with P1
processes[0].has_token = True

current_index = 0

circulation_active = True


# ==========================================
# DISPLAY CURRENT TOKEN HOLDER
# ==========================================

def display_token_holder():

    print("\n========== TOKEN STATUS ==========")

    print(
        f"Current token holder: "
        f"P{processes[current_index].process_id}"
    )

    print(
        "Circulation:",
        "Active" if circulation_active else "Stopped"
    )

    print("==================================")


# ==========================================
# DISPLAY ALL PROCESS STATUSES
# ==========================================

def display_all_status():

    print("\n========== ALL PROCESS STATUSES ==========")

    for process in processes:

        process.display_status()

    print("\n==========================================")


# ==========================================
# SELECT PROCESS
# ==========================================

def select_process():

    while True:

        try:
            pid = int(
                input(f"Select process (1-{n}): ")
            )

            if 1 <= pid <= n:
                return processes[pid - 1]

            print("Invalid process number.")

        except ValueError:
            print("Enter a valid number.")


# ==========================================
# PASS TOKEN TO NEXT PROCESS
# ==========================================

def pass_token():

    global current_index

    if not circulation_active:

        print("\nToken circulation is stopped.")
        print("Restart circulation before passing the token.")
        return

    current_process = processes[current_index]

    next_index = (current_index + 1) % n

    next_process = processes[next_index]

    # Current process releases token
    current_process.has_token = False

    print(
        f"\nToken moves from P{current_process.process_id} "
        f"to P{next_process.process_id}"
    )

    # Update token holder
    current_index = next_index

    # Next process receives token
    next_process.receive_token()

    print(
        f"\nNew token holder: P{next_process.process_id}"
    )


# ==========================================
# MAIN MENU
# ==========================================

while True:

    print("\n============== MAIN MENU ==============")

    print("1. Request Critical Section")
    print("2. Cancel Critical Section Request")
    print("3. Pass Token to Next Process")
    print("4. Stop Token Circulation")
    print("5. Restart Token Circulation")
    print("6. Display Current Token Holder")
    print("7. Display All Process Statuses")
    print("8. Exit Simulation")

    choice = input("\nEnter your choice: ").strip()


    # --------------------------------------
    # 1. REQUEST CS
    # --------------------------------------

    if choice == "1":

        process = select_process()

        process.request_critical_section()


    # --------------------------------------
    # 2. CANCEL REQUEST
    # --------------------------------------

    elif choice == "2":

        process = select_process()

        process.cancel_request()


    # --------------------------------------
    # 3. PASS TOKEN
    # --------------------------------------

    elif choice == "3":

        pass_token()


    # --------------------------------------
    # 4. STOP CIRCULATION
    # --------------------------------------

    elif choice == "4":

        if circulation_active:

            circulation_active = False

            print("\nToken circulation stopped.")

            print(
                f"Token remains with P"
                f"{processes[current_index].process_id}"
            )

        else:

            print("\nToken circulation is already stopped.")


    # --------------------------------------
    # 5. RESTART CIRCULATION
    # --------------------------------------

    elif choice == "5":

        if not circulation_active:

            circulation_active = True

            print("\nToken circulation restarted.")

        else:

            print("\nToken circulation is already active.")


    # --------------------------------------
    # 6. DISPLAY TOKEN HOLDER
    # --------------------------------------

    elif choice == "6":

        display_token_holder()


    # --------------------------------------
    # 7. DISPLAY ALL STATUSES
    # --------------------------------------

    elif choice == "7":

        display_all_status()


    # --------------------------------------
    # 8. EXIT
    # --------------------------------------

    elif choice == "8":

        print("\nExiting Ring-Based Token Simulator.")

        display_token_holder()
        display_all_status()

        break


    else:

        print("\nInvalid choice. Please select 1-8.")
