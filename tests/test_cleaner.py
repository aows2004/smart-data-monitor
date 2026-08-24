from processing.cleaner import ProductCleaner


def test_clean_products():
    products = [
        {
            "name": "  Laptop A  ",
            "price": "£899.99",
            "availability": "In stock",
            "url": "https://shop/a"
        },
        {
            "name": "Laptop B",
            "price": "£599.50",
            "availability": "Out of stock",
            "url": "https://shop/b"
        }
    ]

    df = ProductCleaner().clean(products)

    assert len(df) == 2

    assert df.loc[0, "name"] == "Laptop A"
    assert df.loc[0, "price"] == 899.99
    assert bool(df.loc[0, "availability"]) is True

    assert df.loc[1, "price"] == 599.50
    assert bool(df.loc[1, "availability"]) is False
def test_duplicate_products_are_removed():
    products = [
        {
            "name": "Laptop A",
            "price": "£899.99",
            "availability": "In stock",
            "url": "https://shop/a"
        },
        {
            "name": "Laptop A duplicate",
            "price": "£899.99",
            "availability": "In stock",
            "url": "https://shop/a"
        }
    ]

    df = ProductCleaner().clean(products)

    assert len(df) == 1
def test_empty_product_list():
    df = ProductCleaner().clean([])

    assert df.empty
def test_supports_multiple_price_formats():
    cleaner = ProductCleaner()

    products = [
        {
            "name": "Product A",
            "price": "£47.82",
            "availability": "In stock",
            "url": "https://example.com/a"
        },
        {
            "name": "Product B",
            "price": "$1,299.99",
            "availability": "In stock",
            "url": "https://example.com/b"
        },
        {
            "name": "Product C",
            "price": "€79,95",
            "availability": "In stock",
            "url": "https://example.com/c"
        },
        {
            "name": "Product D",
            "price": "€1.299,99",
            "availability": "In stock",
            "url": "https://example.com/d"
        }
    ]

    df = cleaner.clean(products)

    assert df["price"].tolist() == [
        47.82,
        1299.99,
        79.95,
        1299.99
    ]
def test_supports_multiple_availability_formats():
    cleaner = ProductCleaner()

    products = [
        {
            "name": "A",
            "price": "$10",
            "availability": "Available",
            "url": "https://example.com/a"
        },
        {
            "name": "B",
            "price": "$20",
            "availability": "Only 3 left",
            "url": "https://example.com/b"
        },
        {
            "name": "C",
            "price": "$30",
            "availability": "Out of stock",
            "url": "https://example.com/c"
        },
        {
            "name": "D",
            "price": "$40",
            "availability": "Sold out",
            "url": "https://example.com/d"
        },
        {
            "name": "E",
            "price": "$50",
            "availability": "Not available",
            "url": "https://example.com/e"
        },
        {
            "name": "F",
            "price": "$60",
            "availability": "Reserved",
            "url": "https://example.com/f"
        },
        {
            "name": "G",
            "price": "$70",
            "availability": "Sold",
            "url": "https://example.com/g"
        }
            ]

    df = cleaner.clean(products)

    assert df["availability"].tolist() == [
        True,
        True,
        False,
        False,
        False,
        False,
        False
    ]