import sys
import json
import time

sys.path.append(".")

from ringBuffer import RingBuffer
import order_book


ring = RingBuffer("orders.dat", create=False)

book = order_book.OrderBook("TEST")

current_seq = 0

orders_processed = 0
orders_with_fills = 0
total_fills = 0

print("Starting live OrderBook processor...")
print("Waiting for new orders...")


while True:

    records, current, lost = ring.read_new(current_seq)

    if records:

        print("New orders:", len(records))

        for seq, order in records:

            fills = book.add_limit_order(
                order.order_id,
                order.price,
                order.quantity,
                order.side
            )

            orders_processed += 1

            if fills:
                orders_with_fills += 1
                total_fills += len(fills)

        current_seq = current

        best_bid = book.best_bid()
        best_ask = book.best_ask()
        spread = book.spread()
        depth = book.depth(5)

        snapshot = {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "depth": depth,
            "orders_processed": orders_processed,
            "orders_with_fills": orders_with_fills,
            "total_fills": total_fills
        }

        with open("book_snapshot.json", "w") as f:
            json.dump(snapshot, f)

        print("Orders processed:", orders_processed)
        print("Orders with fills:", orders_with_fills)
        print("Total fills:", total_fills)

    time.sleep(0.1)