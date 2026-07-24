def add_item(items, item):
    items.append(item)
    return items


def add_many(items, values):
    for value in values:
        add_item(items, value)
    return items
