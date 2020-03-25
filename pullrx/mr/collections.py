

# a predicate returns True or False and can raise ReductionDone to halt processing
class ReductionDone(Exception):
    pass


def reduce_list(list_to_reduce, predicate):
    reduced = []
    for item in list_to_reduce:
        try:
            if predicate(item):
                reduced.append(item)
        except ReductionDone:
            break

    return reduced


def sum_list(list_to_sum, predicate):
    return len(reduce_list(list_to_sum, predicate))


def collect_dict_keys(keys, *dicts, require_keys=True, flatten=True):
    collected = []
    for d in dicts:
        for key in keys:
            value = d[key] if require_keys else d.get(key)
            if value is not None:
                val_type = type(value)
                if flatten and val_type in [list, set]:
                    collected.extend(value)
                else:
                    collected.append(value)
    return collected


def filter_dict(dict_to_filer, predicate):
    filtered = {}
    for k, v in dict_to_filer:
        try:
            if predicate(k, v):
                filtered[k] = v
        except ReductionDone:
            break

    return filtered
