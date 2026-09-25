import mmap
import os
import struct
from dataclasses import dataclass
from enum import IntEnum


class Side(IntEnum):
    BUY = 0
    SELL = 1


@dataclass
class Order:
    order_id: int
    price: float
    quantity: int
    side: int  # Side.BUY / Side.SELL (or plain 0/1)

    def side_str(self) -> str:
        return "BUY" if self.side == Side.BUY else "SELL"


class RingBuffer:
    MAGIC = b"RBUF"

    HEADER_FMT = "<4sIQQ"           # magic, slot_size, capacity, write_seq
    HEADER_SIZE = struct.calcsize(HEADER_FMT)

    RECORD_FMT = "<QdIB3x"          # order_id, price, quantity, side, pad
    RECORD_SIZE = struct.calcsize(RECORD_FMT)

    _OFF_WRITE_SEQ = struct.calcsize("<4sIQ")  # offset of write_seq in header

    def __init__(self, path: str, capacity: int = 200_000, create: bool = False):
        self.path = path
        if create:
            self._create(path, capacity)
        else:
            self._open(path)

    # setup

    def _create(self, path: str, capacity: int):
        self.capacity = capacity
        total_size = self.HEADER_SIZE + capacity * self.RECORD_SIZE

        self._fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o644)
        os.ftruncate(self._fd, total_size)
        self._mm = mmap.mmap(self._fd, total_size)
        self._write_header(write_seq=0)

    def _open(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        with open(path, "rb") as f:
            header_bytes = f.read(self.HEADER_SIZE)
        magic, slot_size, capacity, _ = struct.unpack(self.HEADER_FMT, header_bytes)

        self._fd = os.open(path, os.O_RDWR)

        if magic != self.MAGIC:
            raise ValueError(f"{path} is not a valid ring buffer file")
        if slot_size != self.RECORD_SIZE:
            raise ValueError("record layout mismatch between reader and writer")

        self.capacity = capacity
        total_size = self.HEADER_SIZE + capacity * self.RECORD_SIZE
        self._mm = mmap.mmap(self._fd, total_size)

    def _write_header(self, write_seq: int):
        self._mm[: self.HEADER_SIZE] = struct.pack(
            self.HEADER_FMT, self.MAGIC, self.RECORD_SIZE, self.capacity, write_seq
        )

    # shared sequence number

    @property
    def write_seq(self) -> int:
        return struct.unpack_from("<Q", self._mm, self._OFF_WRITE_SEQ)[0]

    def _set_write_seq(self, value: int):
        struct.pack_into("<Q", self._mm, self._OFF_WRITE_SEQ, value)

    def _slot_offset(self, seq: int) -> int:
        return self.HEADER_SIZE + (seq % self.capacity) * self.RECORD_SIZE

    # producer side

    def push(self, order: Order):
        """Write one order into raw bytes, then publish it."""
        seq = self.write_seq
        offset = self._slot_offset(seq)
        struct.pack_into(
            self.RECORD_FMT,
            self._mm,
            offset,
            order.order_id,
            order.price,
            order.quantity,
            int(order.side),
        )
        self._set_write_seq(seq + 1)  # publish

    def flush(self):
        self._mm.flush()

    # consumer side

    def read_slot(self, seq: int) -> Order:
        offset = self._slot_offset(seq)
        order_id, price, quantity, side = struct.unpack_from(
            self.RECORD_FMT, self._mm, offset
        )
        return Order(order_id, price, quantity, side)

    def read_new(self, from_seq: int):
        current = self.write_seq
        lost = 0

        if current - from_seq > self.capacity:
            lost = (current - from_seq) - self.capacity
            from_seq = current - self.capacity

        records = [(seq, self.read_slot(seq)) for seq in range(from_seq, current)]
        return records, current, lost

    def close(self):
        self._mm.close()
        os.close(self._fd)