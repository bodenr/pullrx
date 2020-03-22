from pullrx.mr import collections


META_DELIM = '__'


class MemoryStore(object):
    # a dict like struct that maintains separate metadata about its contents

    def __init__(self, identifier):
        self._store = {}
        self._meta = {}
        self.set_meta('id', identifier)

    @property
    def identifier(self):
        return self.get_meta('id')

    def keys(self, include_meta=False):
        if not include_meta:
            return self._store.keys()
        d = self._meta.copy()
        d.update(self._store)
        return d.keys()

    def values(self, include_meta=False):
        if not include_meta:
            return self._store.values()
        d = self._meta.copy()
        d.update(self._store)
        return d.values()

    def items(self, include_meta=False):
        if not include_meta:
            return self._store.items()
        d = self._meta.copy()
        d.update(self._store)
        return d.items()

    def update_from_array(self, array_of_dicts, dict_key):
        for d in array_of_dicts:
            self._store[d[dict_key]] = d

    def update(self, other_store, include_meta=False):
        self._store.update(other_store._store)
        if include_meta:
            self._meta.update(other_store._meta)

    @staticmethod
    def to_meta_key(key):
        if not key.startswith(META_DELIM):
            key = META_DELIM + key
        if not key.endswith(META_DELIM):
            key += META_DELIM

        return key

    def __setitem__(self, key, value):
        if MemoryStore.is_meta_key(key):
            return self.set_meta(key, value)
        return self.set(key, value)

    def __getitem__(self, key):
        if MemoryStore.is_meta_key(key):
            return self._meta[key]
        return self._store[key]

    @staticmethod
    def is_meta_key(key):
        return key.startswith(META_DELIM) and key.endswith(META_DELIM)

    def set_meta(self, meta_key, meta_val):
        meta_key = MemoryStore.to_meta_key(meta_key)

        old_val = self._meta.get(meta_key)
        self._meta[meta_key] = meta_val

        return old_val

    def set(self, key, val):
        old_val = self._store.get(key)
        self._store[key] = val
        return old_val

    def get(self, key, default_value=None):
        return self._store.get(key, default_value)

    def get_meta(self, meta_key, default_val=None):
        return self._meta.get(MemoryStore.to_meta_key(meta_key), default_val)

    def set_keyed_path(self, key_path, item):
        keys = MemoryStore.keyed_paths(key_path)
        last_key = keys.pop(-1)

        store_map = self._store
        for store_key in keys:
            if store_key not in store_map:
                store_map[store_key] = {}
            store_map = store_map[store_key]

        store_map[last_key] = item

    @staticmethod
    def keyed_paths(key_path):
        # a path of keys separate by ':'
        return key_path.split(':')

    @staticmethod
    def build_keyed_path(*path_keys):
        return ':'.join(path_keys)

    def get_keyed_path(self, key_path):
        store_map = self._store

        for key in MemoryStore.keyed_paths(key_path):
            store_map = store_map[key]

        return store_map

    def filter(self, predicate, include_meta=False):
        filtered = collections.filter_dict(self._store, predicate)
        if include_meta:
            filtered.update(collections.filter_dict(self._meta, predicate))

        return filtered

    def __contains__(self, item):
        return item in self._store or item in self._meta

    def __str__(self):
        d = self._meta.copy()
        d.update(self._store)
        return str(d)
