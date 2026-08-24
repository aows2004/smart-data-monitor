import pandas as pd
import pytest

from processing.validator import (
    ScrapeValidationError,
    ScrapeValidator
)


def make_products(count):
    return pd.DataFrame([
        {
            "name": f"Product {i}",
            "price": float(i + 10),
            "availability": True,
            "url": f"https://shop/{i}"
        }
        for i in range(count)
    ])


def test_valid_first_scrape():
    new_df = make_products(20)

    validator = ScrapeValidator()

    assert validator.validate(new_df) is True


def test_rejects_empty_scrape():
    new_df = pd.DataFrame(
        columns=[
            "name",
            "price",
            "availability",
            "url"
        ]
    )

    validator = ScrapeValidator()

    with pytest.raises(ScrapeValidationError):
        validator.validate(new_df)


def test_rejects_suspicious_product_drop():
    previous_df = make_products(100)
    new_df = make_products(40)

    validator = ScrapeValidator(
        maximum_drop_ratio=0.5
    )

    with pytest.raises(ScrapeValidationError):
        validator.validate(
            new_df,
            previous_df
        )


def test_accepts_reasonable_product_drop():
    previous_df = make_products(100)
    new_df = make_products(80)

    validator = ScrapeValidator(
        maximum_drop_ratio=0.5
    )

    assert validator.validate(
        new_df,
        previous_df
    ) is True