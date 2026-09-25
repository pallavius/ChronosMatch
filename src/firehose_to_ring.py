from order_generator import generate_orders
from ringBuffer import RingBuffer, Order, Side

ring = RingBuffer("orders.dat", capacity=1000, create=True)
