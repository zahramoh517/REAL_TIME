import psycopg
import heapq
import redis as rd
import time

conn = psycopg.connect(
    dbname="postgres",
    user="zahra",
    host="localhost",
    port=5432
)
cur = conn.cursor()

cur.execute("""
    SELECT * FROM events;
""")

rows = cur.fetchall()

cur.close()
conn.close()


def dictCreation(rows):
    shipment_lists = {}
    for row in rows:
        shipment_id = row[1]
        if shipment_id not in shipment_lists:
            shipment_lists[shipment_id] = []
        shipment_lists[shipment_id].append(row)


    return shipment_lists

import heapq

def merge_shipments(shipment_lists):
    heap = []

    for shipment_id, entries in shipment_lists.items():
        heapq.heappush(heap, (entries[0][2], shipment_id)) #first time then shipID
    

    merged = []

    while heap:
        timestamp, shipment_id = heapq.heappop(heap)   
        row = shipment_lists[shipment_id].pop(0)      
        merged.append(row)                             

        if shipment_lists[shipment_id]:                
            next_timestamp = shipment_lists[shipment_id][0][2] 
            heapq.heappush(heap, (next_timestamp, shipment_id)) #

    return merged

def redis_merge_shipments(merged):
    r = rd.Redis(host='localhost', port=6379, db=0)

    for row in merged:
        event = r.xadd('events_stream', {'event_id': str(row[0]), 'shipment_id': str(row[1]), 'timestamp': row[2].strftime('%Y-%m-%d %H:%M:%S'), 'lat': row[3], 'lon': row[4], 'hub_name': row[5] if row[5] is not None else ""})  
        time.sleep(0.5) #give some time to process the events in the streaem

if __name__ == "__main__":
    shipment_lists = dictCreation(rows)
    merged = merge_shipments(shipment_lists)
    redis_merge_shipments(merged)
