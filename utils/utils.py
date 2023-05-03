import h5py
import math
from itertools import combinations

def roundup_duration_to_simulation_timestep(duration, timestep):
    return timestep * math.ceil(duration/timestep)

def roundup(duration, timestep):
    return roundup_duration_to_simulation_timestep(duration, timestep)

def slots_to_secs(slots, slot_length, timestep):
    # return roundup(slots * slot_length, timestep)
    return slots * slot_length

def secs_to_slots(duration, slot_length):
    return math.ceil(duration / slot_length)

class CachedDataset(object):
    """Wrapper around default h5py Dataset that accelerates single index access to the data.

    hdf5 loads data 'lazily', i.e. only loads data into memory that is explicitly indexed. This incurs high
    delays when accessing single values successively. Chunk caching should improve this, but we couldn't observe
    a gain. Instead, this class implements a simple cached dataset, where data is read into memory in blocks
    and single index access reads from that cache.

    Args:
        dataset: underlying hdf5 dataset
        cache_size: number of values to be held in memory
    """

    def __init__(self, dataset: h5py.Dataset, cache_size: int = 10_000_000):
        self._ds = dataset
        self._istart = 0
        self._iend = -1
        self._cache_size = cache_size

    def __getitem__(self, key):
        if isinstance(key, slice):
            return self._ds[key]
        elif isinstance(key, int):
            return self.get_cached(key)

    def __len__(self):
        return len(self._ds)

    def update_cache(self, idx):
        self._istart = (idx // self._cache_size) * self._cache_size
        self._iend = min(len(self._ds), self._istart + self._cache_size)
        self._buf = self._ds[self._istart : self._iend]

    def get_cached(self, idx):
        if idx >= self._istart and idx < self._iend:
            return self._buf[idx - self._istart]
        else:
            self.update_cache(idx)
            return self.get_cached(idx)

class DataReader(object):
    """Convenient and cached access to an hdf5 database with power traces from multiple nodes."""

    def __init__(self, path, cache_size=10_000_000):
        self.path = path
        self.cache_size = cache_size
        self._datasets = dict()

        self._hf = h5py.File(self.path, "r")
        self.nodes = list(self._hf["data"].keys())

        self.time = self._hf["time"]
        for node in self._hf["data"].keys():
            self._datasets[node] = CachedDataset(self._hf["data"][node], self.cache_size)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._datasets[f"node{key}"]
        else:
            return self._datasets[key]

    def __len__(self):
        return len(self.time)

    def pairs(self):
        """Returns all unique combinations between the nodes in this database."""
        return combinations(range(len(self.nodes)), 2)
    
    def get_dist_model(self, node):
        """Returns the charging time distribution of the specified node

        Args:
            node (string): Name of the node

        Returns:
            (string): Name of the charging time distribution
        """

        return self._hf["data"][node].attrs["model"]