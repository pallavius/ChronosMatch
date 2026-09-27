import asyncio

from order_generator import create_order
from ringBuffer import RingBuffer, Order, Side


async def main():

    ring = RingBuffer("orders.dat", capacity=1000, create=True)

    number_of_orders = 100_000

    for order_id in range(1, number_of_orders + 1):

        order_data = create_order(order_id)

        side = Side.BUY if order_data["side"] == "BUY" else Side.SELL

        order = Order(
            order_id=order_data["order_id"],
            price=order_data["price"],
            quantity=order_data["quantity"],
            side=side
        )

        ring.push(order)

        # Give the OrderBook process a chance to read new orders
        if order_id % 100 == 0:
            ring.flush()
            await asyncio.sleep(0)

    ring.flush()
    ring.close()

    print("All orders pushed into ring buffer.")


if __name__ == "__main__":
    asyncio.run(main())