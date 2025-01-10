import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def store_chunk_metadata(file_id, chunk_id, offset, size, storage_path):
    r.rpush(f"file:{file_id}:chunks", chunk_id)
    r.hmset(f"chunk:{chunk_id}", {
        "offset": offset,
        "size": size,
        "storage_path": storage_path
    })

def get_chunk_list(file_id, page, size):
    start = (page - 1) * size
    end = start + size - 1
    chunk_ids = r.lrange(f"file:{file_id}:chunks", start, end)
    
    chunks = []
    for chunk_id in chunk_ids:
        chunk_data = r.hgetall(f"chunk:{chunk_id.decode()}")
        chunks.append({
            "chunkID": chunk_id.decode(),
            "offset": int(chunk_data[b'offset']),
            "size": int(chunk_data[b'size']),
            "storagePath": chunk_data[b'storage_path'].decode()
        })

    return chunks