

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


def filter_dict(dict_to_filer, predicate):
    filtered = {}
    for k, v in dict_to_filer:
        try:
            if predicate(k, v):
                filtered[k] = v
        except ReductionDone:
            break

    return filtered
