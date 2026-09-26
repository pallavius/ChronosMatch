# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# distutils: language = c++
from cython.operator cimport dereference as deref, preincrement as inc
from libc.stdint cimport int64_t, uint8_t


cdef class OrderBook:

    def __cinit__(self, str symbol="SYMBOL"):
        self.symbol = symbol
        self._next_seq = 0

    def __len__(self):
        return self._index.size()

    cdef int64_t _tick(self) noexcept nogil:
        self._next_seq += 1
        return self._next_seq

    cdef vector[Fill] _match(self, COrder& taker) noexcept nogil:
        cdef vector[Fill] fills
        cdef Fill f
        cdef PriceLevels* opposite
        cdef PriceLevels.iterator it
        cdef PriceLevel* level
        cdef COrder* maker
        cdef double level_price
        cdef int64_t trade_qty
        cdef bint tradable

        if taker.side == SIDE_BUY:
            opposite = &self._asks
        else:
            opposite = &self._bids

        while taker.quantity > 0:
            it = opposite.begin()
            if it == opposite.end():
                break

            level = &deref(it).second

            if taker.side == SIDE_BUY:
                level_price = deref(it).first       
                tradable = level_price <= taker.price
            else:
                level_price = -deref(it).first        
                tradable = level_price >= taker.price

            if not tradable:
                break

            while (not level.empty()) and taker.quantity > 0:
                maker = &level.front()
                if taker.quantity < maker.quantity:
                    trade_qty = taker.quantity
                else:
                    trade_qty = maker.quantity

                f.maker_order_id = maker.order_id
                f.taker_order_id = taker.order_id
                f.price = level_price                 
                f.quantity = trade_qty
                f.aggressor_side = taker.side
                fills.push_back(f)

                taker.quantity -= trade_qty
                maker.quantity -= trade_qty

                if maker.quantity == 0:
                    self._index.erase(maker.order_id)
                    level.pop_front()


            if level.empty():
                opposite.erase(it)

        return fills

    cdef void _rest(self, COrder order) noexcept nogil:
        cdef OrderLocation loc
        cdef double key

        if order.side == SIDE_BUY:
            key = -order.price
            self._bids[key].push_back(order)
        else:
            key = order.price
            self._asks[key].push_back(order)

        loc.key = key
        loc.side = order.side
        self._index[order.order_id] = loc

    cdef bint _cancel(self, int64_t order_id) noexcept nogil:
        cdef unordered_map[int64_t, OrderLocation].iterator idx_it
        cdef PriceLevels* book
        cdef PriceLevels.iterator lvl_it
        cdef PriceLevel* level
        cdef PriceLevel.iterator ord_it
        cdef OrderLocation loc

        idx_it = self._index.find(order_id)
        if idx_it == self._index.end():
            return False
        loc = deref(idx_it).second

        book = &self._bids if loc.side == SIDE_BUY else &self._asks
        lvl_it = book.find(loc.key)
        if lvl_it == book.end():
            self._index.erase(idx_it)
            return False

        level = &deref(lvl_it).second
        ord_it = level.begin()
        while ord_it != level.end():
            if deref(ord_it).order_id == order_id:
                level.erase(ord_it)
                break
            inc(ord_it)

        if level.empty():
            book.erase(lvl_it)

        self._index.erase(idx_it)
        return True

    cdef void _best(self, PriceLevels& book, bint negate_key, double* price,
                     int64_t* qty, bint* found) noexcept nogil:
        cdef PriceLevels.iterator it = book.begin()
        cdef PriceLevel.iterator lit
        cdef int64_t total

        if it == book.end():
            found[0] = False
            return

        price[0] = -deref(it).first if negate_key else deref(it).first
        total = 0
        lit = deref(it).second.begin()
        while lit != deref(it).second.end():
            total += deref(lit).quantity
            inc(lit)
        qty[0] = total
        found[0] = True


    cpdef list add_limit_order(self, int64_t order_id, double price,
                                int64_t quantity, uint8_t side):

        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if side != SIDE_BUY and side != SIDE_SELL:
            raise ValueError("side must be 0 (buy) or 1 (sell)")

        cdef COrder taker
        cdef vector[Fill] fills
        cdef Fill f
        cdef size_t i

        taker.order_id = order_id
        taker.price = price
        taker.quantity = quantity
        taker.side = side
        taker.seq = 0

        with nogil:
            fills = self._match(taker)
            if taker.quantity > 0:
                taker.seq = self._tick()
                self._rest(taker)

        result = []
        for i in range(fills.size()):
            f = fills[i]
            result.append({
                "maker_order_id": f.maker_order_id,
                "taker_order_id": f.taker_order_id,
                "price": f.price,
                "quantity": f.quantity,
                "aggressor_side": "BUY" if f.aggressor_side == SIDE_BUY else "SELL",
            })
        return result

    cpdef list add_limit_orders_batch(self, list orders):
        cdef Py_ssize_t n = len(orders)
        cdef vector[COrder] batch
        cdef vector[Fill] all_fills
        cdef vector[Fill] fills
        cdef COrder o
        cdef Py_ssize_t i, j
        cdef Fill f

        batch.reserve(n)
        for i in range(n):
            order_id, price, quantity, side = orders[i]
            o.order_id = order_id
            o.price = price
            o.quantity = quantity
            o.side = side
            o.seq = 0
            batch.push_back(o)

        with nogil:
            for i in range(n):
                fills = self._match(batch[i])
                for j in range(<Py_ssize_t>fills.size()):
                    all_fills.push_back(fills[j])
                if batch[i].quantity > 0:
                    batch[i].seq = self._tick()
                    self._rest(batch[i])

        result = []
        for i in range(<Py_ssize_t>all_fills.size()):
            f = all_fills[i]
            result.append({
                "maker_order_id": f.maker_order_id,
                "taker_order_id": f.taker_order_id,
                "price": f.price,
                "quantity": f.quantity,
                "aggressor_side": "BUY" if f.aggressor_side == SIDE_BUY else "SELL",
            })
        return result

    cpdef bint cancel_order(self, int64_t order_id):
        """Remove a resting order. Returns True if it was found and removed."""
        cdef bint ok
        with nogil:
            ok = self._cancel(order_id)
        return ok

    cpdef object best_bid(self):
        """(price, total_quantity) of the best bid, or None."""
        cdef double price
        cdef int64_t qty
        cdef bint found
        with nogil:
            self._best(self._bids, True, &price, &qty, &found)
        return (price, qty) if found else None

    cpdef object best_ask(self):
        """(price, total_quantity) of the best ask, or None."""
        cdef double price
        cdef int64_t qty
        cdef bint found
        with nogil:
            self._best(self._asks, False, &price, &qty, &found)
        return (price, qty) if found else None

    cpdef object spread(self):
        """best_ask - best_bid, or None if either side is empty."""
        bid = self.best_bid()
        ask = self.best_ask()
        if bid is None or ask is None:
            return None
        return ask[0] - bid[0]

    cpdef list depth(self, int levels=5):
        """
        Top `levels` price levels on each side, as
        {"bids": [(price, total_qty), ...], "asks": [(price, total_qty), ...]}
        with bids sorted best-first (highest price) and asks best-first
        (lowest price).
        """
        cdef PriceLevels.iterator it
        cdef PriceLevel.iterator lit
        cdef int64_t total
        cdef int n

        bids = []
        it = self._bids.begin()
        n = 0
        while it != self._bids.end() and n < levels:
            total = 0
            lit = deref(it).second.begin()
            while lit != deref(it).second.end():
                total += deref(lit).quantity
                inc(lit)
            bids.append((-deref(it).first, total))
            inc(it)
            n += 1

        asks = []
        it = self._asks.begin()
        n = 0
        while it != self._asks.end() and n < levels:
            total = 0
            lit = deref(it).second.begin()
            while lit != deref(it).second.end():
                total += deref(lit).quantity
                inc(lit)
            asks.append((deref(it).first, total))
            inc(it)
            n += 1

        return [{"bids": bids, "asks": asks}]

    def __repr__(self):
        return f"OrderBook({self.symbol!r}, resting_orders={len(self)})"
