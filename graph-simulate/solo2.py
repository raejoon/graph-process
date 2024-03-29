import random
from constants import INTERVAL

CONFIG_PATH_VECTOR = True
CONFIG_CLAMPING = True

JITTER = 10
ALPHA = 50

class SoloNode(object):
    """ Solo Node behaves in the following manner.
        1. When it starts, it broadcasts a beacon and reschedules a broadcast
           for INTERVAL after.
        2. Any reception before its first broadcast is ignored.
        3. Whenever it broadcasts, it sends is node id and degree.
        4. If it receives a beacon, it updates the source node's offset in the
           neighbor map. If the node does not exist in the map, it is added.
        5. After the sender node's offset is updated, it checks the offset
           distance between the sender's offset and its offset. If the sender
           has a deficit, the node (the receiver) reschedules the pending
           broadcast with a delay between 0 and INTERVAL/2.
        6. Path vector loop detection is implemented.
        7. Target broadcast time is limited by the successor's broadcast time.
    """
    def __init__(self, node_id, pq):
        self.node_id = node_id
        self.pq = pq
        self.neighbor_map = {}
        self.links = set([])

        # State
        self.on = False
        self.my_slot = False
        self.latest_broadcast = None
        self.next_broadcast = None
        self.timer_task = None
        self.path_vector = []
        
        # Logging related
        self.log = []
        self.log.append((0, self.node_id, "init", "None"))

        self.random = random.Random(node_id)


    def set_links(self, node_list):
        self.links = set(node_list)


    def start(self, aux):
        self.on = True
        self.broadcast()
        self.set_timer(INTERVAL)
        self.next_broadcast = self.now() + INTERVAL


    def now(self):
        return self.pq.current


    def close_slot(self):
        now = self.now()
        target_share = self.target_share()
        my_share = now - self.latest_broadcast
        deficit = (target_share - my_share) / target_share
        self.log.append((now, self.node_id, "deficit", str(deficit)))
        self.my_slot = False

    
    def broadcast(self):
        now = self.now()
        degree = len(self.neighbor_map)
        pv_string = self.pathvector_to_string(self.path_vector)
        for neighbor in self.links:
            task = (neighbor.recv_callback, (self.node_id, degree, pv_string))
            self.pq.add_task(task, now)

        self.path_vector = [] 
        self.log.append((now, self.node_id, "broadcast", "None"))
        if self.my_slot:
            self.close_slot()
        self.my_slot = True
        self.latest_broadcast = now


    def recv_callback(self, src, deg, pv_str):
        if not self.on:
            return

        if self.my_slot:
            self.close_slot()
        
        now = self.now()
        self.neighbor_map[src] = now
        src_pv = self.string_to_pathvector(pv_str)
        self.adjust(src, deg, src_pv)


    def timer_callback(self, aux):
        self.broadcast()
        self.set_timer(INTERVAL)
        self.next_broadcast = self.now() + INTERVAL


    def set_timer(self, interval):
        self.timer_task = (self.timer_callback, (None,))
        interval += self.random.randint(-JITTER, JITTER)
        self.pq.add_task(self.timer_task, self.now() + interval)


    def adjust(self, your_id, your_degree, your_pv): 
        now = self.now() 
        next_bc = self.next_broadcast

        target_share = INTERVAL // (max(your_degree, 1) + 1)
        your_share = next_bc - now
        if your_share - target_share > -1e-3 * INTERVAL:
            return

        if CONFIG_PATH_VECTOR:
            if len(your_pv) > 0 and self.node_id in your_pv:
                self.path_vector = []
                self.log.append((now, self.node_id, "reset", "None"))
                self.on = False
                self.pq.remove_task(self.timer_task)
                reset_time = now + self.random.randint(0, INTERVAL - 1)
                self.pq.add_task((self.start, (None,)), reset_time)
                return
            else:
                self.path_vector = your_pv + [your_id]

        target_bc = now + target_share

        if CONFIG_CLAMPING:
            successor_bc = self.get_successor_expiry()
            if target_bc > successor_bc: 
                target_bc = successor_bc

        new_bc = (next_bc * (100 - ALPHA) + target_bc * ALPHA) // 100
        
        self.next_broadcast = new_bc
        self.set_timer(self.next_broadcast - now)


    def target_share(self):
        return INTERVAL // (len(self.neighbor_map) + 1)


    def pathvector_to_string(self, path_vector):
        if len(path_vector) == 0:
            return ""
        else:
            return ",".join(str(i) for i in path_vector)


    def string_to_pathvector(self, string):
        path_vector = []
        if string != "":
            path_vector = [int(s) for s in string.split(",")]
        return path_vector


    def get_successor_expiry(self):
        offsets = [t % INTERVAL for t in self.neighbor_map.values()]
        distance = [self.diff(o, self.next_broadcast) for o in offsets]
        return self.next_broadcast + min(distance) 
         

    def diff(self, a, b):
        return (a + INTERVAL - b) % INTERVAL
