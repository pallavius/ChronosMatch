##ChronosMatch — Low-Latency Order Matching Engine

ChronosMatch is a low-latency order matching engine prototype built to explore high-performance order processing, inter-process communication (IPC), memory-mapped shared memory, and optimized order matching using Python and Cython.

The project combines an asynchronous market order generator, a memory-mapped ring buffer, a Cython-based order book, performance measurements, and a real-time dashboard.

##Project Overview

ChronosMatch simulates a simplified financial market in which generated buy and sell orders are transferred between processes, processed by an order book, and matched according to price-time priority.

#The project focuses on:

Efficient order generation and processing

Inter-process communication using memory-mapped shared memory

Order-book matching and trade generation

Latency and throughput measurement

IPC performance comparison

Market visualization through a dashboard


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
          +-------------------+
          |                   |
          v                   v
     Trade Buffer        SQLite Writer
          |                   |
          +---------+---------+
                    |
                    v
          Market Dashboard / Metrics
```


The exact data path depends on the script being executed. The separate IPC proof benchmark compares mmap and pickle-based IPC and does not run the Cython matching engine.


## Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core programming language |
| asyncio | Asynchronous order generation |
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


##Main Components

#1. Market Firehose

The market firehose generates synthetic market orders asynchronously.

Each order includes fields such as:

order_id — unique order identifier

price — order price

quantity — number of units

side — BUY or SELL

The generator can be benchmarked independently to measure order-generation performance.

#2. Memory-Mapped Ring Buffer

The ring buffer transfers order data between processes through a memory-mapped file.

Its purpose is to reduce the overhead associated with repeatedly serializing and transferring Python objects between processes.

The implementation uses binary records and shared-memory access to support high-volume order delivery.

#3. Cython Order Book

The order book processes incoming orders and matches compatible buy and sell orders.

The matching engine is implemented in Cython to reduce Python-level overhead in performance-sensitive operations.

The project explores price-time priority, where better-priced orders take precedence and orders at the same price are handled according to arrival order.

#4. Trade Buffer and SQLite

The trade buffer provides storage for generated trade records. The project also includes SQLite-based trade-writing support.

Trade buffering and successful persistence to SQLite are separate concerns; the database record count should be verified independently when validating persistence.

#5. Dashboard

The browser-based dashboard presents market information and engine metrics, including:

Bid and ask market depth

Best bid and best ask

Bid-ask spread

Order-book information

Latency and throughput metrics where supplied by the running engine

Market status and alert indicators

The dashboard is intended to make the matching engine's activity easier to inspect during demonstrations.

## Repository Structure

```text
ChronosMatch/
├── src/
│   ├── dashboard.py
│   ├── firehose_to_ring.py
│   ├── firehose_to_ring_concurrent.py
│   ├── order_book.pyx
│   ├── order_book.cpp
│   ├── order_book.cp312-win_amd64.pyd
│   ├── order_generator.py
│   ├── ring_to_orderbook.py
│   ├── ringBuffer.py
│   ├── run_engine_audit.py
│   ├── run_live_demo.py
│   ├── test_ring_reader.py
│   ├── trade_buffer.py
│   └── trade_writer.py
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
│   ├── verify_integrity.py
│   └── proof_results.json
├── static/
|    |___ style1.css
├── templates/
|    |___ dashboard.html
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

##Installation and Setup

##Prerequisites

Windows 10 or Windows 11

Python 3.12

Git

Visual Studio Build Tools with the Desktop development with C++ workload for compiling Cython extensions

#1. Clone the repository

git clone https://github.com/DivyaL-1/ChronosMatch.git
cd ChronosMatch

If the repository is already cloned, open its folder instead of cloning it again.

#2. Create a virtual environment

python -m venv .venv

Activate it in PowerShell:

.\.venv\Scripts\Activate.ps1

#3. Install dependencies

If the repository contains requirements.txt, run:

python -m pip install --upgrade pip
pip install -r requirements.txt

Install any additional project-specific dependencies listed in the relevant scripts or build configuration.

#4. Compile the Cython extension

The Cython extension must be built before running scripts that import the compiled order-book module.

Use the project's existing build configuration, such as setup.py or pyproject.toml, if available. For a compatible setup.py configuration, the command is typically:

python setup.py build_ext --inplace

Run the build from the directory containing the build configuration. If your repository uses a different build system, follow that configuration instead.

##Running the Project

Run commands from the repository root unless otherwise indicated.

#Run the browser dashboard

python app.py

Open the local URL printed by Flask in your browser. The default Flask address is commonly http://127.0.0.1:5000, unless the application is configured differently.

#Run the order generator

python src/order_generator.py

This runs the generator's configured default workload. Check the script if you need to change the order count or benchmark settings.

#Run the producer and ring-buffer workflow

python src/firehose_to_ring.py

This script uses the configuration defined in the source file. Ensure the consumer is started as required by the particular workflow before running a producer-only script.

#Run the matching-engine audit

python src/run_engine_audit.py

This runs the audit with the count and configuration currently defined in the script.

#Run the live demonstration

python src/run_live_demo.py

Use the workflow's expected startup order and configuration so the producer and consumer coordinate correctly.

#Run the one-million-order IPC proof test

python test/run_proof.py

The default test sends 1,000,000 orders through each of two IPC implementations:

Memory-mapped shared memory (mmap)

Pickle-based IPC using multiprocessing.connection

The test compares elapsed wall-clock time, combined CPU time, throughput, and reported lost orders. It writes its results to test/proof_results.json.

The IPC proof test is separate from the Cython matching-engine audit.
