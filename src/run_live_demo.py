
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
    ring = RingBuffer(
        str(ROOT / "orders.dat"),
        capacity=CAPACITY,
        create=True
    )
    ring.close()

    consumer = subprocess.Popen(
        [sys.executable, str(SRC / "ring_to_orderbook.py")],
        cwd=str(ROOT)
    )

    try:
        time.sleep(0.5)

        subprocess.run(
            [
                sys.executable,
                str(SRC / "firehose_to_ring_concurrent.py"),
                "--count", str(COUNT),
                "--delay", "0.02"
            ],
            cwd=str(ROOT),
            check=True
        )

        consumer.wait(timeout=120)

    finally:
        if consumer.poll() is None:
            consumer.terminate()
            consumer.wait()


if __name__ == "__main__":
    main()

