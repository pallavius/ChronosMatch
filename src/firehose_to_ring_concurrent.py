
import argparse
import asyncio

from order_generator import create_order
from ringBuffer import RingBuffer, Order, Side


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100_000)
    parser.add_argument("--delay", type=float, default=0)
    args = parser.parse_args()

    ring = RingBuffer("orders.dat", create=False)

    try:
        for order_id in range(1, args.count + 1):
            data = create_order(order_id)
            side = Side.BUY if data["side"] == "BUY" else Side.SELL

            ring.push(Order(
                order_id=data["order_id"],
                price=data["price"],
                quantity=data["quantity"],
                side=side
            ))

            if order_id % 100 == 0:
                ring.flush()
                await asyncio.sleep(args.delay)

        ring.flush()
        print(f"Producer completed: {args.count:,} orders written.")
    finally:
        ring.close()


if __name__ == "__main__":
    asyncio.run(main())
