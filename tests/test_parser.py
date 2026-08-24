from pathlib import Path
from config import ScrapeConfig
from processing.parser import ProductParser
from pathlib import Path

from config import (
    BOOKS_TO_SCRAPE_CONFIG,
    ScrapeConfig
)

from processing.parser import ProductParser


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "sample_catalog.html"
)
ALT_FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "sample_store_alt.html"
)


ALT_STORE_CONFIG = ScrapeConfig(
    product_selector="div.store-item",
    name_selector=".item-name",
    price_selector=".cost",
    availability_selector=".stock-status",
    link_selector=".item-link",
    next_page_selector=".pagination-next"
)


def load_fixture():
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parser_extracts_products():
    html = load_fixture()

    products = ProductParser(BOOKS_TO_SCRAPE_CONFIG).parse(
        html,
        "https://example.com/"
    )

    assert len(products) == 2

    assert products[0]["name"] == "Laptop A"
    assert products[0]["price"] == "£899.99"
    assert products[0]["availability"] == "In stock"

    assert products[0]["url"] == (
        "https://example.com/"
        "catalogue/laptop-a/index.html"
    )


def test_parser_finds_next_page():
    html = load_fixture()

    next_url = ProductParser(BOOKS_TO_SCRAPE_CONFIG).get_next_page_url(
        html,
        "https://example.com/catalogue/"
    )

    assert next_url == (
        "https://example.com/catalogue/page-2.html"
    )
def test_parser_supports_different_site_structure():
    html = ALT_FIXTURE_PATH.read_text(
        encoding="utf-8"
    )

    parser = ProductParser(
        ALT_STORE_CONFIG
    )

    products = parser.parse(
        html,
        "https://store.example.com/"
    )

    assert len(products) == 2

    assert products[0]["name"] == "Phone X"
    assert products[0]["price"] == "$799.99"
    assert products[0]["availability"] == "Available"

    assert products[0]["url"] == (
        "https://store.example.com/products/phone-x"
    )

    next_url = parser.get_next_page_url(
        html,
        "https://store.example.com/"
    )

    assert next_url == (
        "https://store.example.com/products/page/2"
    )
def test_parser_supports_optional_fields():
    config = ScrapeConfig(
        product_selector=".product",
        name_selector=".name",
        price_selector=".price",
        link_selector=".name"
    )

    html = """
    <html>
    <body>
        <div class="product">
            <a
                class="name"
                href="/product-a"
            >
                Product A
            </a>

            <span class="price">
                $25.00
            </span>
        </div>
    </body>
    </html>
    """

    parser = ProductParser(config)

    products = parser.parse(
        html,
        "https://example.com/"
    )

    assert len(products) == 1
    assert products[0]["name"] == "Product A"
    assert products[0]["availability"] == "Unknown"

    assert (
        products[0]["url"]
        == "https://example.com/product-a"
    )

    assert (
        parser.get_next_page_url(
            html,
            "https://example.com/"
        )
        is None
    )