class MessageQueue:
    def __init__(self):
        self.queue = []
        
    def enqueue(self, message):
        # Menambahkan pesan baru ke antrean
        self.queue.append(message)
        
    def dequeue(self):
        # Mengambil pesan terdepan dari antrean
        if not self.is_empty():
            return self.queue.pop(0)
        return None
        
    def peek(self):
        # Melihat pesan terdepan tanpa mengambilnya
        if not self.is_empty():
            return self.queue[0]
        return None
        
    def is_empty(self):
        # Memeriksa apakah antrean kosong
        return len(self.queue) == 0
        
    def size(self):
        # Mendapatkan jumlah pesan dalam antrean
        return len(self.queue)

# Contoh penggunaan
message_system = MessageQueue()

# Mengirim beberapa pesan
message_system.enqueue({"id": 1, "from": "Alice", "to": "Bob", "content": "Halo Bob!", "timestamp": "10:00"})
message_system.enqueue({"id": 2, "from": "Charlie", "to": "Bob", "content": "Apa kabar?", "timestamp": "10:01"})
message_system.enqueue({"id": 3, "from": "David", "to": "Alice", "content": "Meeting jam berapa?", "timestamp": "10:02"})

# Memproses pesan berdasarkan urutan masuk
while not message_system.is_empty():
    current_message = message_system.dequeue()
    print(f"Memproses pesan: {current_message['id']} dari {current_message['from']} ke {current_message['to']}")
    # Di sini kita bisa menambahkan logika pemrosesan pesan