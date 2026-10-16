
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

sys.path.insert(0, str(SRC))
from ringBuffer import RingBuffer

COUNT = 100_000
CAPACITY = 120_000


def main():
    ring_path = ROOT / "orders.dat"
    snapshot_path = ROOT / "book_snapshot.json"

    # Create a fresh, sufficiently large shared buffer.
    ring = RingBuffer(
        str(ring_path),
        capacity=CAPACITY,
        create=True
    )
    ring.close()

    consumer_cmd = [
        sys.executable, str(SRC / "ring_to_orderbook.py")
    ]
    producer_cmd = [
        sys.executable,
        str(SRC / "firehose_to_ring_concurrent.py"),
        "--count", str(COUNT)
    ]

    start = time.perf_counter()

    print("Starting OrderBook consumer...")
    consumer = subprocess.Popen(
        consumer_cmd,
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        # Give the consumer time to open the initialized buffer.
        time.sleep(0.3)

        print("Starting concurrent order producer...")
        producer = subprocess.Popen(
            producer_cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            prod_out, prod_err = producer.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            producer.kill()
            producer.communicate()
            raise RuntimeError("Producer timed out.")

        if producer.returncode != 0:
            raise RuntimeError(f"Producer failed:\n{prod_err}")

        try:
            cons_out, cons_err = consumer.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            consumer.kill()
            consumer.communicate()
            raise RuntimeError("Consumer timed out before finishing.")

        if consumer.returncode != 0:
            raise RuntimeError(f"Consumer failed:\n{cons_err}")

        elapsed = time.perf_counter() - start

        print("\n--- Producer output ---")
        print(prod_out.strip())

        print("\n--- OrderBook output ---")
        print(cons_out.strip())

        if not snapshot_path.exists():
            raise RuntimeError("book_snapshot.json was not created.")

        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

        processed = snapshot["orders_processed"]
        lost = snapshot["orders_lost"]

        print("\n--- Concurrent Integration Audit ---")
        print(f"Expected orders:  {COUNT:,}")
        print(f"Processed orders: {processed:,}")
        print(f"Reported lost:   {lost:,}")
        print(f"Total fills:     {snapshot['total_fills']:,}")
        print(f"Elapsed time:    {elapsed:.4f} seconds")
        print(f"End-to-end rate: {processed / elapsed:,.0f} orders/sec")

        if processed != COUNT or lost != 0:
            raise RuntimeError(
                "AUDIT FAILED: processed count mismatch or lost records."
            )

        print("\nAUDIT PASSED: all expected orders were processed.")

    finally:
        if consumer.poll() is None:
            consumer.terminate()
            consumer.wait()


if __name__ == "__main__":
    main()
