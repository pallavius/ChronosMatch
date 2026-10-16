
import sys
import json
import time
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ringBuffer import RingBuffer
import order_book

EXPECTED_ORDERS = 100_000


def percentile(values, percent):
    """Return the nearest-rank percentile."""
    if not values:
        return 0

    ordered = sorted(values)
    index = math.ceil((percent / 100) * len(ordered)) - 1
    return ordered[max(0, index)]


def main():
    ring = RingBuffer("orders.dat", create=False)
    book = order_book.OrderBook("TEST")

    current_seq = 0
    orders_processed = 0
    orders_with_fills = 0
    total_fills = 0
    total_lost = 0

    # Store each order-processing duration in nanoseconds.
    latencies_ns = []

    start_ns = time.perf_counter_ns()

    print("Starting ChronosMatch engine audit...")

    try:
        while orders_processed < EXPECTED_ORDERS:
            records, current, lost = ring.read_new(current_seq)
            total_lost += lost

            if records:
                for seq, order in records:
                    # Start timing immediately before entering the engine.
                    entry_ns = time.perf_counter_ns()

                    fills = book.add_limit_order(
                        order.order_id,
                        order.price,
                        order.quantity,
                        order.side
                    )

                    # Stop timing immediately after the engine call returns.
                    exit_ns = time.perf_counter_ns()

                    latency_ns = exit_ns - entry_ns
                    latencies_ns.append(latency_ns)

                    orders_processed += 1

                    if fills:
                        orders_with_fills += 1
                        total_fills += len(fills)

                current_seq = current

            else:
                time.sleep(0.01)

        end_ns = time.perf_counter_ns()
        elapsed_ns = end_ns - start_ns
        elapsed_seconds = elapsed_ns / 1_000_000_000

        average_latency_ns = (
            sum(latencies_ns) / len(latencies_ns)
            if latencies_ns else 0
        )

        snapshot = {
            "best_bid": book.best_bid(),
            "best_ask": book.best_ask(),
            "spread": book.spread(),
            "depth": book.depth(5),
            "orders_processed": orders_processed,
            "orders_with_fills": orders_with_fills,
            "total_fills": total_fills,
            "orders_lost": total_lost,
            "elapsed_seconds": elapsed_seconds,
            "throughput_orders_per_sec": (
                orders_processed / elapsed_seconds
                if elapsed_seconds > 0 else 0
            ),
            "latency_measurement": "book.add_limit_order call duration",
            "average_latency_ns": average_latency_ns,
            "p95_latency_ns": percentile(latencies_ns, 95),
            "p99_latency_ns": percentile(latencies_ns, 99),
            "min_latency_ns": min(latencies_ns) if latencies_ns else 0,
            "max_latency_ns": max(latencies_ns) if latencies_ns else 0
        }

        with open(ROOT / "book_snapshot.json", "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)

        print("\n--- ChronosMatch Engine Audit ---")
        print(f"Expected orders:       {EXPECTED_ORDERS:,}")
        print(f"Orders processed:      {orders_processed:,}")
        print(f"Orders lost:           {total_lost:,}")
        print(f"Orders with fills:     {orders_with_fills:,}")
        print(f"Total fills:           {total_fills:,}")
        print(f"Elapsed seconds:       {elapsed_seconds:.4f}")
        print(
            f"Throughput:            "
            f"{snapshot['throughput_orders_per_sec']:,.0f} orders/sec"
        )

        print("\n--- Order Processing Latency ---")
        print(f"Average latency:       {average_latency_ns:,.0f} ns")
        print(f"P95 latency:           {snapshot['p95_latency_ns']:,} ns")
        print(f"P99 latency:           {snapshot['p99_latency_ns']:,} ns")
        print(f"Minimum latency:       {snapshot['min_latency_ns']:,} ns")
        print(f"Maximum latency:       {snapshot['max_latency_ns']:,} ns")

        print("\nSnapshot saved to book_snapshot.json")

        if orders_processed != EXPECTED_ORDERS or total_lost:
            print("AUDIT FAILED: order count mismatch or records lost.")
            sys.exit(1)

        print("AUDIT PASSED: all expected orders were processed.")

    finally:
        ring.close()


if __name__ == "__main__":
    main()
