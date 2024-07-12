
class DetourTable:
    def __init__(self, sat_num, orbit_num):
        self.table = {f'SAT-{j}-{i}': set() for i in range(sat_num) for j in range(orbit_num)}

    def add(self, id, v):
        self.table[id].add(v)

    def erase(self, id, v):
        self.table[id].discard(v)

    def has(self, id, v):
        return v in self.table[id]

