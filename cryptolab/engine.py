"""Replay declining sale prices and fill bounded demand while reconciling token inventory and proceeds."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    start = integer(d["start"])
    duration = integer(d["duration"], 1)
    high = integer(d["start_price"], 1)
    low = integer(d["end_price"], 1)
    inventory = integer(d["inventory"])
    initial = inventory
    raised = 0
    rows = []
    if low > high:
        raise ValueError("price must decline")
    for order in chronology(d["orders"]):
        t = order["timestamp"]
        budget = integer(order["budget"])
        wanted = integer(order["wanted"])
        maxprice = integer(order["max_price"], 1)
        if t < start:
            raise ValueError("sale not started")
        price = high - (high - low) * min(t - start, duration) // duration
        fill = 0 if price > maxprice else min(wanted, budget // price, inventory)
        cost = fill * price
        inventory -= fill
        raised += cost
        rows.append(
            {
                "timestamp": t,
                "price": price,
                "filled": fill,
                "cost": cost,
                "refund": budget - cost,
            }
        )
    return {
        "orders": rows,
        "sold": initial - inventory,
        "remaining": inventory,
        "proceeds": raised,
    }


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
