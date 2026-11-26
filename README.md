# Distributed Systems Algorithms

Small Python demonstrations of distributed-systems concepts, including clock synchronization, logical clocks, message ordering, mutual exclusion, and termination detection.

## Requirements

- Python 3
- No third-party packages are required.

Run commands from the project directory:

```text
python <script-name>.py
```

Several scripts prompt for input; the others run a short example and print the results.

## Examples

| File | Demonstration |
| --- | --- |
| `berkeley.py` | Berkeley clock synchronization: adjusts sample clocks toward their average. |
| `cristian.py` | Cristian's clock synchronization algorithm with example network delays. |
| `ntp.py` | NTP-style offset and round-trip delay calculations using four timestamps. |
| `lamport_logical_clock.py` | Lamport logical clocks for events and message sends/receives. |
| `clock_vector.py` | Interactive normal vector-clock simulator with internal events and queued messages. |
| `reduced_vector_clock.py` | Interactive sparse vector-clock simulator. |
| `casual_ordering.py` | Interactive causal message-ordering simulator using vector clocks. |
| `bss.py` | Causal broadcast example that buffers messages until their causal predecessors are delivered. |
| `MX_Lamport.py` | Lamport distributed mutual exclusion with request, reply, and release messages. |
| `ricart_agrawala.py` | Ricart–Agrawala mutual exclusion with deferred replies. |
| `ring_algorithm.py` | Interactive ring-based token mutual exclusion simulator. |
| `Huang.py` | Multi-process simulation of Huang's distributed termination-detection algorithm. |

## Running Huang's simulation

`Huang.py` starts one node per process. Open a separate terminal for each node, change to this project directory, and start every node with the same total-node count. For a three-node simulation:

```text
python Huang.py 0 3
python Huang.py 1 3
python Huang.py 2 3
```

Run each command in its own terminal. Node IDs start at `0`; Node `0` is the root. Nodes communicate over TCP on `127.0.0.1`, using ports starting at `6001` (Node 0 uses port `6001`, Node 1 uses `6002`, and so on). Allow these local ports to be available.

At the root prompt, configure the parent-child tree, synchronize it to the workers, and start work:

```text
add 0 1
add 0 2
sync
start 1
```

Type `help` in a node's prompt to see its available commands. For example, workers can use `send <child>` to send work to a child and `passive` to become passive. The root reports global termination when the computation's credit has returned.

## Notes

- These are educational simulations and examples, not production distributed-system implementations.
- Most examples model message delivery locally rather than communicating over a network. `Huang.py` is the exception and uses local TCP connections.