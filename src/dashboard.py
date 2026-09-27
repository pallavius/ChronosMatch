import curses
import time
import json
import os


def dashboard(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)

    while True:
        stdscr.clear()

        height, width = stdscr.getmaxyx()

        snapshot_path = "book_snapshot.json"

        if not os.path.exists(snapshot_path):
            stdscr.addstr(5, 5, "Waiting for OrderBook data...")
            stdscr.refresh()
            time.sleep(1)
            continue

        try:
            with open(snapshot_path, "r") as f:
                snapshot = json.load(f)

            best_bid = snapshot["best_bid"]
            best_ask = snapshot["best_ask"]
            spread = snapshot["spread"]

            depth = snapshot["depth"][0]

            bids = depth["bids"]
            asks = depth["asks"]

            orders_processed = snapshot["orders_processed"]
            orders_with_fills = snapshot["orders_with_fills"]
            total_fills = snapshot["total_fills"]

        except (json.JSONDecodeError, KeyError, OSError):
            stdscr.addstr(5, 5, "Waiting for valid OrderBook data...")
            stdscr.refresh()
            time.sleep(0.5)
            continue

        # Header
        stdscr.addstr(1, 5, "========================================")
        stdscr.addstr(2, 5, "       CHRONOSMATCH - MARKET")
        stdscr.addstr(3, 5, "========================================")

        # Order book
        stdscr.addstr(5, 10, "ORDER BOOK")

        stdscr.addstr(7, 10, "BID")
        stdscr.addstr(7, 30, "ASK")

        stdscr.addstr(8, 10, "--------------------")
        stdscr.addstr(8, 30, "--------------------")

        for i in range(min(5, len(bids), len(asks))):
            stdscr.addstr(
                9 + i,
                10,
                f"{bids[i][0]:.2f}  Qty: {bids[i][1]}"
            )

            stdscr.addstr(
                9 + i,
                30,
                f"{asks[i][0]:.2f}  Qty: {asks[i][1]}"
            )

        # Best prices
        stdscr.addstr(
            15,
            10,
            f"Best Bid: {best_bid[0]:.2f}  Qty: {best_bid[1]}"
        )

        stdscr.addstr(
            16,
            10,
            f"Best Ask: {best_ask[0]:.2f}  Qty: {best_ask[1]}"
        )

        stdscr.addstr(
            17,
            10,
            f"Spread:   {spread:.2f}"
        )

        # Statistics
        stdscr.addstr(19, 10, f"Orders Processed: {orders_processed}")
        stdscr.addstr(20, 10, f"Orders With Fills: {orders_with_fills}")
        stdscr.addstr(21, 10, f"Total Fills:      {total_fills}")

        stdscr.addstr(23, 10, "----------------------------------------")
        stdscr.addstr(24, 10, "Status: LIVE")
        stdscr.addstr(25, 10, "Press Q to quit")

        stdscr.refresh()

        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            break

        time.sleep(0.5)


if __name__ == "__main__":
    curses.wrapper(dashboard)