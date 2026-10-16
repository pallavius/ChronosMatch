# ChronosMatch

ChronosMatch is a low-latency trading-engine prototype that simulates
market-order generation, transfers order records through a memory-mapped
ring buffer, processes them with a Cython-based OrderBook, and displays
market statistics in a terminal dashboard.

> **Project status:** The main components have been implemented and
> basic matching has been tested. Large-scale IPC validation and
> reliable end-to-end performance benchmarking remain future work.

## Architecture

``` text
Market Firehose
      |
      v
Memory-Mapped Ring Buffer (mmap + struct)
      |
      v
Ring-to-OrderBook Processor
      |
      v
Cython OrderBook
      |
      v
JSON Snapshot
      |
      v
Curses Terminal Dashboard
```

## Main Components

-   **Market Firehose** (`src/firehose_to_ring.py`): generates simulated
    BUY and SELL orders and writes them to the ring buffer.
-   **Order Generator** (`src/order_generator.py`): creates mock order
    data.
-   **Ring Buffer** (`src/ringBuffer.py`): stores fixed-layout binary
    records in a memory-mapped file.
-   **OrderBook** (`src/order_book.pyx`, `src/order_book.pxd`):
    Cython-based order matching implementation.
-   **Processor** (`src/ring_to_orderbook.py`): reads buffered orders,
    sends them to the OrderBook, and writes market statistics to
    `book_snapshot.json`.
-   **Dashboard** (`src/dashboard.py`): displays the latest snapshot in
    the terminal.
-   **Verification Test** (`test_engine_verification.py`): checks a
    simple BUY/SELL matching scenario.

## Technology Stack

-   Python
-   asyncio
-   `mmap` and `struct`
-   Cython
-   JSON
-   curses (`windows-curses` on Windows)

## Setup

Run the following commands from the project root in PowerShell.

### 1. Create and activate a virtual environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

Install the dependencies listed in your project's requirements file if
one is available. The build also requires Cython and setuptools. For
example:

``` powershell
python -m pip install --upgrade pip setuptools Cython
python -m pip install windows-curses
```

Install any other packages imported by the project that are not already
available in the environment.

### 3. Build the Cython extension

``` powershell
python setup_test.py build_ext --inplace
```

A successful build should create a compiled `order_book` extension in
the project root. The exact filename depends on your Python version and
platform.

## Running the Pipeline

Open separate PowerShell terminals for the producer, processor, and
dashboard. Activate the same virtual environment in each terminal.

### 1. Start the processor

``` powershell
python src\ring_to_orderbook.py
```

### 2. Generate and write orders

In another terminal:

``` powershell
python src\firehose_to_ring.py
```

The firehose script currently generates 100,000 simulated orders. The
ring buffer in this setup has a capacity of 1,000 records, so if the
producer writes all orders before the consumer reads them, older records
can be overwritten. The number of records actually processed depends on
producer/consumer timing and the ring-buffer implementation.

### 3. Start the dashboard

In a third terminal:

``` powershell
python src\dashboard.py
```

The dashboard reads `book_snapshot.json`. Keep the terminal window large
enough for the dashboard layout. Use the dashboard's displayed quit key
to exit.

> **Important:** Do not run a process that recreates or truncates
> `orders.dat` while another process is using it. Stop the producer and
> consumer before restarting the pipeline if you encounter file or
> memory-mapping errors.

## Run the Matching Verification

After building the Cython extension, run:

``` powershell
python test_engine_verification.py
```

The verification test inserts a BUY order at 150.00 for 100 units,
followed by a compatible SELL order at 149.00 for 100 units. The
expected result is a fill for 100 units at the resting BUY order's
price, 150.00, and a PASS message.

## Output

The processor writes a `book_snapshot.json` file containing market
statistics such as:

-   Best bid
-   Best ask
-   Spread
-   Bid and ask depth
-   Orders processed
-   Orders with fills
-   Total fills

The dashboard reads this snapshot and presents the values in the
terminal.

## Performance Notes

-   A previously recorded generation-only benchmark was approximately
    **412,000 generated orders per second**. This is not end-to-end
    system throughput.
-   A single matching-call timing was recorded at **13,800 nanoseconds
    (0.0138 ms)**. This is one measurement, not a statistically reliable
    latency benchmark.
-   A run that writes 100,000 orders to a 1,000-slot ring buffer without
    concurrent consumption can overwrite 99,000 earlier records. This
    demonstrates a capacity/consumer-rate limitation, not successful
    processing of all 100,000 orders.
-   The one-million-order IPC audit and comprehensive end-to-end latency
    testing should be reported as complete only after their results have
    been verified.

## Known Limitations and Future Work

-   Improve ring-buffer capacity and overflow/data-loss handling.
-   Perform the planned one-million-order IPC audit.
-   Collect repeated latency measurements, including median and tail
    latency.
-   Benchmark end-to-end throughput rather than order generation alone.
-   Add persistent trade logging, for example with SQLite or ClickHouse.
-   Add highlighting for large or unusual orders to the dashboard.

## Repository Notes

Generated files such as `orders.dat`, `book_snapshot.json`, compiled
extensions (`.pyd`), and build outputs may be runtime artifacts. Check
`.gitignore` before committing them.

## Disclaimer

ChronosMatch is a project prototype for learning and evaluation. It is
not a production trading system and has not been validated for
real-money trading.
