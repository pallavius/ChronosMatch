# ChronosMatch – Low-Latency Order Matching Engine

ChronosMatch is a low-latency order matching engine prototype developed to explore high-performance order processing, inter-process communication (IPC), memory-mapped shared memory, and optimized order matching using Python and Cython.

The project combines an asynchronous market order generator, a memory-mapped ring buffer, a Cython-based order book, trade generation, performance benchmarking, and a web-based market dashboard.

## Project Overview

ChronosMatch simulates a simplified financial market in which generated buy and sell orders are transferred between processes, processed by an order book, and matched according to price-time priority.

The main objectives are:

- Generate synthetic market orders asynchronously.
- Transfer orders efficiently between processes.
- Implement a memory-mapped ring buffer for IPC.
- Process and match orders using a Cython-based order book.
- Generate and buffer trades.
- Measure processing latency and throughput.
- Compare mmap-based IPC with pickle-based IPC.
- Visualize market activity through a dashboard.

## Architecture

```text
              Async Market Firehose
                       |
                       v
              Generated Market Orders
                       |
                       v
              Memory-Mapped Ring Buffer
                       |
                       v
                Order Book Consumer
                       |
                       v
               Cython Matching Engine
                       |
                       v
                 Price-Time Priority
                       |
                       v
                  Trade Generation
                       |
             +---------+---------+
             |                   |
             v                   v
        Trade Buffer        SQLite Writer
             |                   |
             +---------+---------+
                       |
                       v
             Market Dashboard / Metrics
```

The main matching-engine workflow processes orders through the ring buffer and order book. The separate IPC proof test compares mmap and pickle-based communication using independent producer and consumer processes.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core programming language |
| asyncio | Asynchronous market order generation |
| Cython | Optimized order-book processing |
| NumPy | Numerical and array operations, where applicable |
| mmap | Memory-mapped shared memory for IPC |
| struct | Binary order data representation |
| Flask | Web-based dashboard |
| HTML | Dashboard structure |
| CSS | Dashboard styling |
| SQLite | Trade storage and persistence |
| Git | Version control |
| GitHub | Source code hosting and collaboration |
| PowerShell | Windows development and execution |

## Main Components

### 1. Async Market Firehose

The market firehose generates synthetic market orders asynchronously.

Each generated order contains:

- `order_id` – Unique order identifier.
- `price` – Price of the order.
- `quantity` – Number of units.
- `side` – Order direction (`BUY` or `SELL`).

The generator supports configurable order counts and can be benchmarked independently to measure generation performance.

### 2. Memory-Mapped Ring Buffer

The ring buffer transfers order data between separate processes using memory-mapped files.

It uses binary data representation to reduce the overhead associated with transferring serialized Python objects.

Key concepts include:

- Shared-memory communication.
- Memory-mapped file access.
- Binary record storage.
- Producer-consumer coordination.
- High-volume order delivery.

### 3. Cython Matching Engine

The order book is implemented using Cython to improve performance in order-processing operations.

It supports buy and sell orders and performs matching based on price-time priority.

The matching process considers:

- Best available bid and ask prices.
- Order quantities.
- Order-side information.
- Matching and fill generation.

Cython is used to reduce Python-level overhead in performance-sensitive operations.

### 4. Trade Buffer and SQLite Writer

The trade buffer stores generated trade records using memory-mapped storage.

The project also includes an SQLite writer for trade persistence.

This separates trade generation, buffering, and database-writing responsibilities.

### 5. Web-Based Market Dashboard

The Flask-based dashboard provides a visual representation of market activity.

Dashboard features include:

- Bid and ask order-book depth.
- Best bid and best ask prices.
- Bid-ask spread.
- Market information.
- Latency and throughput metrics, where available.
- Market status and alert indicators.

HTML and CSS are used to build the dashboard interface.

## Repository Structure

```text
ChronosMatch/
│
├── src/
│   ├── dashboard.py
│   ├── firehose_to_ring.py
│   ├── firehose_to_ring_concurrent.py
│   ├── order_book.pyx
│   ├── order_book.cpp
│   ├── order_generator.py
│   ├── ring_to_orderbook.py
│   ├── ringBuffer.py
│   ├── run_engine_audit.py
│   ├── run_live_demo.py
│   ├── test_ring_reader.py
│   ├── trade_buffer.py
│   └── trade_writer.py
│
├── test/
│   ├── cpu_timing.py
│   ├── gen.py
│   ├── ipc_address.py
│   ├── mmap_consumer.py
│   ├── mmap_producer.py
│   ├── pickle_consumer.py
│   ├── pickle_producer.py
│   ├── ringBuffer.py
│   ├── run_proof.py
│   └── verify_integrity.py
│
├── tests/
│
├── static/
│   └── style1.css
│
├── templates/
│   └── dashboard.html
│
├── app1.py
├── setup_test.py
├── test_engine_verification.py
├── test_order_book.py
├── book_snapshot.json
├── orders.dat
├── trades.dat
├── trades.db
├── .gitignore
└── README.md
```

Generated files, compiled extensions, and runtime data files may be created during execution and are not source-code dependencies.

## Installation and Setup

### Prerequisites

- Windows 10 or Windows 11.
- Python 3.12.
- Git.
- Visual Studio Build Tools with the **Desktop development with C++** workload.
- Cython and the dependencies required by the project.

### 1. Clone the repository

```powershell
git clone https://github.com/DivyaL-1/ChronosMatch.git
cd ChronosMatch
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

If a `requirements.txt` file is available in the repository:

```powershell
pip install -r requirements.txt
```

Otherwise, install the dependencies specified by the project's setup configuration.

### 5. Build the Cython extension

Run the project's build configuration from the appropriate directory.

For a project using `setup.py`, the typical command is:

```powershell
python setup.py build_ext --inplace
```

The compiled extension must be available before running scripts that import the Cython order book.

## Running the Project

Run commands from the project root unless otherwise specified.

### Start the Web Dashboard

```powershell
python app.py
```

Open the local URL displayed in the terminal to view the dashboard.

### Run the Order Generator

```powershell
python src/order_generator.py
```

### Run the Firehose-to-Ring-Buffer Workflow

```powershell
python src/firehose_to_ring.py
```

### Run the Matching-Engine Audit

```powershell
python src/run_engine_audit.py
```

### Run the Live Demonstration

```powershell
python src/run_live_demo.py
```

### Run the One-Million-Order IPC Proof Test

```powershell
python test/run_proof.py
```

The proof test compares two IPC implementations:

1. Memory-mapped shared memory (mmap).
2. Pickle-based IPC using `multiprocessing.connection`.

The default workload is 1,000,000 orders for each method.

The test generates a `proof_results.json` file containing benchmark results.

## Performance Benchmarks

The following results were obtained during actual project test runs.

Performance may vary depending on hardware, system load, Python version, and execution conditions.

### 1. Matching-Engine Audit – 100,000 Orders

| Metric | Result |
|---|---:|
| Expected Orders | 100,000 |
| Orders Processed | 100,000 |
| Reported Lost Orders | 0 |
| Orders With Fills | 42,734 |
| Total Fills | 77,959 |
| Trades Buffered | 77,959 |
| Elapsed Time | 1.7148 seconds |
| Throughput | 58,315 orders/second |
| Average Latency | 1,943 ns |
| P95 Latency | 3,500 ns |
| P99 Latency | 7,400 ns |
| Maximum Latency | 1,625,600 ns |

**Latency measurement:** These latency values measure the duration of an individual `book.add_limit_order()` call. They do not represent end-to-end latency across order generation, IPC, matching, and persistence.

The maximum recorded matching-call latency was approximately 1.626 milliseconds.

### 2. Concurrent IPC Audit – 100,000 Orders

| Metric | Result |
|---|---:|
| Expected Orders | 100,000 |
| Orders Processed | 100,000 |
| Reported Lost Orders | 0 |
| Total Fills | 77,959 |
| Elapsed Time | 2.1867 seconds |
| Throughput | 45,732 orders/second |

This is a separate concurrent IPC benchmark and should not be confused with the matching-engine audit.

### 3. One-Million-Order IPC Benchmark

The IPC proof test compares memory-mapped shared memory with pickle-based communication using separate producer and consumer processes.

**Test workload: 1,000,000 orders per method.**

| Metric | mmap (Shared Memory) | Pickle-Based IPC |
|---|---:|---:|
| Orders Sent | 1,000,000 | 1,000,000 |
| Wall-Clock Time | 5.453 seconds | 18.268 seconds |
| Combined CPU Time | 6.031 seconds | 27.219 seconds |
| Throughput | 183,372 orders/sec | 54,740 orders/sec |
| Reported Lost Orders | 0 | 0 |

**Benchmark observations:**

- mmap achieved approximately 3.3 times faster wall-clock performance.
- mmap used approximately 4.5 times less combined CPU time.
- Both consumers reported receiving all 1,000,000 orders.
- Both methods reported zero lost orders.

These results demonstrate the performance of the tested IPC implementations. They do not represent one million orders processed by the Cython matching engine.

### Benchmark Interpretation

The project includes different benchmarks for different stages of the system:

| Benchmark | What It Measures |
|---|---|
| Order Generator | Synthetic order-generation performance |
| Matching-Engine Audit | Order-book processing and matching-call latency |
| Concurrent IPC Audit | Producer-consumer processing performance |
| One-Million-Order IPC Proof | mmap versus pickle-based IPC performance |

The results should be interpreted separately because the workloads and measurement methods differ.

## Testing and Verification

The project includes scripts for checking IPC delivery, data integrity, and order-book matching.

Important verification points include:

1. Confirm that the expected order count matches the consumer's processed count.
2. Verify that the reported lost-order count is zero.
3. Check producer and consumer process exit codes.
4. Test buy and sell order matching.
5. Compare generated fills with trade-buffer records.
6. Verify SQLite persistence independently when required.
7. Record benchmark results for reproducibility.

The one-million-order IPC proof test completed successfully in the recorded run.


## Learning Outcomes

Through ChronosMatch, the project explores practical concepts in systems programming and performance engineering:

- Asynchronous programming with Python.
- Inter-process communication.
- Memory-mapped files and ring buffers.
- Binary data representation.
- Cython optimization.
- Order matching and price-time priority.
- Latency and throughput benchmarking.
- Producer-consumer process coordination.
- Data-integrity verification.
- Dashboard development and system monitoring.

## Team Members

**Divya L.**
**Jayendra Kondekar.**
**Pallavi U S.**                                                                                          


Project Repository: [ChronosMatch](https://github.com/pallavius/ChronosMatch)

## Disclaimer

ChronosMatch is an educational and experimental software project developed to explore order matching, IPC, and performance optimization.

It is not intended for live financial trading or production brokerage use. Benchmark results represent specific development runs and are not guarantees of performance on other hardware or workloads.
