def flatten(nested):
    out = []
    for item in nested:
        if isinstance(item, list):
            out.append(flatten(item))
        else:
            out.append(item)
    return out


def count_leaves(nested):
    return len(flatten(nested))
