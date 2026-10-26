
import os
import sys
import json
import time
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from ringBuffer import RingBuffer
from trade_buffer import TradeBuffer, Trade
import order_book

EXPECTED_ORDERS = 100_000
SNAPSHOT_INTERVAL = 1000
WHALE_LEVEL_THRESHOLD = 3


def percentile(values, percent):
    """Return the nearest-rank percentile."""
    if not values:
        return 0

    ordered = sorted(values)
    index = math.ceil((percent / 100) * len(ordered)) - 1
    return ordered[max(0, index)]


def write_snapshot(
    book,
    orders_processed,
    orders_with_fills,
    total_fills,
    last_whale_event=None
):
    """Write the current order-book state for the dashboard."""
    snapshot = {
        "best_bid": book.best_bid(),
        "best_ask": book.best_ask(),
        "spread": book.spread(),
        "depth": book.depth(5),
        "orders_processed": orders_processed,
        "orders_with_fills": orders_with_fills,
        "total_fills": total_fills,
        "last_whale_event": last_whale_event
    }

    snapshot_path = ROOT / "book_snapshot.json"

    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f)

def main():
    ring = RingBuffer("orders.dat", create=False)
    trade_buffer = None

    try:
        book = order_book.OrderBook("TEST")

        trade_buffer = TradeBuffer(
            str(ROOT / "trades.dat"),
            capacity=100_000,
            create=True
        )

        current_seq = 0
        orders_processed = 0
        orders_with_fills = 0
        total_fills = 0
        total_lost = 0
        trades_buffered = 0

        latencies_ns = []
        last_whale_event = None
        start_ns = time.perf_counter_ns()

        print("Starting ChronosMatch engine audit...")

        while orders_processed < EXPECTED_ORDERS:
            records, current, lost = ring.read_new(current_seq)
            total_lost += lost

            if records:
                for seq, order in records:
                    entry_ns = time.perf_counter_ns()

                    fills = book.add_limit_order(
                        order.order_id,
                        order.price,
                        order.quantity,
                        order.side
                    )

                    exit_ns = time.perf_counter_ns()
                    latencies_ns.append(exit_ns - entry_ns)

                    orders_processed += 1

                    if fills:
                        orders_with_fills += 1
                        total_fills += len(fills)

                        # Detect executions across multiple price levels.
                        filled_prices = {
                            round(float(fill["price"]), 8)
                            for fill in fills
                        }

                        if len(filled_prices) >= WHALE_LEVEL_THRESHOLD:
                            last_whale_event = {
                                "order_id": order.order_id,
                                "side": (
                                    "BUY"
                                    if order.side in (0, "BUY")
                                    else "SELL"
                                ),
                                "levels_cleared": len(filled_prices),
                                "timestamp": time.strftime("%H:%M:%S")
                            }

                            print(
                                f"\nWHALE ALERT: Order "
                                f"{last_whale_event['order_id']} "
                                f"({last_whale_event['side']}) executed "
                                f"across {last_whale_event['levels_cleared']} "
                                f"price levels at "
                                f"{last_whale_event['timestamp']}!"
                            )

                        # Preserve every fill in the trade buffer.
                        for fill in fills:
                            trade = Trade(
                                maker_order_id=fill["maker_order_id"],
                                taker_order_id=fill["taker_order_id"],
                                price=fill["price"],
                                quantity=fill["quantity"],
                                aggressor_side=(
                                    0 if fill["aggressor_side"] == "BUY"
                                    else 1
                                )
                            )

                            trade_buffer.push(trade)
                            trades_buffered += 1

                    # Publish progress periodically.
                    if orders_processed % SNAPSHOT_INTERVAL == 0:
                        write_snapshot(
                            book,
                            orders_processed,
                            orders_with_fills,
                            total_fills,
                            last_whale_event
                        )

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

        # Final snapshot includes all audit statistics.
        snapshot = {
            "best_bid": book.best_bid(),
            "best_ask": book.best_ask(),
            "spread": book.spread(),
            "depth": book.depth(5),
            "orders_processed": orders_processed,
            "orders_with_fills": orders_with_fills,
            "total_fills": total_fills,
            "trades_buffered": trades_buffered,
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
            "max_latency_ns": max(latencies_ns) if latencies_ns else 0,
            "last_whale_event": last_whale_event
        }

        snapshot_path = ROOT / "book_snapshot.json"

        with open(snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)

        print("\n--- ChronosMatch Engine Audit ---")
        print(f"Expected orders:       {EXPECTED_ORDERS:,}")
        print(f"Orders processed:      {orders_processed:,}")
        print(f"Orders lost:           {total_lost:,}")
        print(f"Orders with fills:     {orders_with_fills:,}")
        print(f"Total fills:           {total_fills:,}")
        print(f"Trades buffered:       {trades_buffered:,}")
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

        if trades_buffered != total_fills:
            print("AUDIT FAILED: trade buffer count mismatch.")
            sys.exit(1)

        print("AUDIT PASSED: all expected orders were processed.")
        print("All reported fills were written to the trade buffer.")

    finally:
        if trade_buffer is not None:
            trade_buffer.flush()
            trade_buffer.close()

        ring.close()


if __name__ == "__main__":
    main()
