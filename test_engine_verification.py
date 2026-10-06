import sys
import time

sys.path.append("src")

import order_book


book = order_book.OrderBook("TEST")


# Add a BUY order
buy_id = 1001
buy_price = 150.00
buy_quantity = 100

print("Adding BUY order...")
print(f"Order ID: {buy_id}")
print(f"Price: {buy_price}")
print(f"Quantity: {buy_quantity}")

buy_fills = book.add_limit_order(
    buy_id,
    buy_price,
    buy_quantity,
    0
)

print("BUY fills:", buy_fills)


# Add a SELL order that can match the BUY
sell_id = 2001
sell_price = 149.00
sell_quantity = 100

print("\nAdding SELL order...")
print(f"Order ID: {sell_id}")
print(f"Price: {sell_price}")
print(f"Quantity: {sell_quantity}")

start = time.perf_counter_ns()

sell_fills = book.add_limit_order(
    sell_id,
    sell_price,
    sell_quantity,
    1
)

end = time.perf_counter_ns()

latency_ns = end - start

print(f"SELL order processed in: {latency_ns} ns")
print(f"SELL order processed in: {latency_ns / 1_000_000:.6f} ms")
print("SELL fills:", sell_fills)


# Verification
print("\n========== ENGINE VERIFICATION ==========")

if sell_fills:
    print("PASS: BUY and SELL orders were matched.")
    print("Fill generated:", sell_fills)
else:
    print("FAIL: No fill was generated.")