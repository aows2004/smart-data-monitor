import pandas as pd

from processing.comparator import ProductComparator


def test_detects_new_removed_and_changed_products():
    old = pd.DataFrame([
        {
            "name": "Laptop A",
            "price": 900.0,
            "availability": True,
            "url": "a"
        },
        {
            "name": "Laptop B",
            "price": 600.0,
            "availability": True,
            "url": "b"
        },
        {
            "name": "Laptop C",
            "price": 400.0,
            "availability": False,
            "url": "c"
        }
    ])

    new = pd.DataFrame([
        {
            "name": "Laptop A",
            "price": 850.0,
            "availability": True,
            "url": "a"
        },
        {
            "name": "Laptop B",
            "price": 600.0,
            "availability": True,
            "url": "b"
        },
        {
            "name": "Laptop D",
            "price": 1100.0,
            "availability": True,
            "url": "d"
        }
    ])

    result = ProductComparator().compare(old, new)

    assert len(result["new"]) == 1
    assert len(result["removed"]) == 1
    assert len(result["changed"]) == 1

    assert result["new"].iloc[0]["name"] == "Laptop D"
    assert result["removed"].iloc[0]["name"] == "Laptop C"

    changed = result["changed"].iloc[0]

    assert changed["old_price"] == 900.0
    assert changed["new_price"] == 850.0