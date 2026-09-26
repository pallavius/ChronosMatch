
from libcpp.map cimport map as cmap
from libcpp.deque cimport deque as cdeque
from libcpp.vector cimport vector
from libcpp.unordered_map cimport unordered_map
from libc.stdint cimport int64_t, uint8_t


cdef enum:
    SIDE_BUY = 0
    SIDE_SELL = 1

cdef struct COrder:
    int64_t order_id
    double price
    int64_t quantity
    uint8_t side
    int64_t seq         


cdef struct Fill:
    int64_t maker_order_id
    int64_t taker_order_id
    double price
    int64_t quantity
    uint8_t aggressor_side

cdef struct OrderLocation:
    double key            
    uint8_t side

ctypedef cdeque[COrder] PriceLevel


ctypedef cmap[double, PriceLevel] PriceLevels


cdef class OrderBook:
    cdef PriceLevels _bids
    cdef PriceLevels _asks
    cdef unordered_map[int64_t, OrderLocation] _index
    cdef int64_t _next_seq
    cdef readonly str symbol


    cdef int64_t _tick(self) noexcept nogil
    cdef vector[Fill] _match(self, COrder& taker) noexcept nogil
    cdef void _rest(self, COrder order) noexcept nogil
    cdef bint _cancel(self, int64_t order_id) noexcept nogil
    cdef void _best(self, PriceLevels& book, bint negate_key, double* price, int64_t* qty, bint* found) noexcept nogil

    
    cpdef list add_limit_order(self, int64_t order_id, double price, int64_t quantity, uint8_t side)
    cpdef bint cancel_order(self, int64_t order_id)
    cpdef object best_bid(self)
    cpdef object best_ask(self)
    cpdef object spread(self)
    cpdef list depth(self, int levels=*)
    cpdef list add_limit_orders_batch(self, list orders)
