from collections import deque

class FixedSizeQueue:
    def __init__(self, max_size):
        self.queue = deque(maxlen=max_size)

    def enqueue(self, item):
        self.queue.append(item)

    def dequeue(self):
        if len(self.queue) > 0:
            removed_item = self.queue.popleft()
            print(f"Dequeued: {removed_item}, Queue: {list(self.queue)}")
            return removed_item
        else:
            print("Queue is empty, nothing to dequeue.")
            return None

    def __str__(self):
        return list(self.queue)



