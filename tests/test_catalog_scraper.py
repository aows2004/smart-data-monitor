from config import BOOKS_TO_SCRAPE_CONFIG
from scraper.catalog_scraper import CatalogScraper


class FakeScraper:
    def __init__(self, pages):
        self.pages = pages
        self.requested_urls = []

    def fetch_page(self, url):
        self.requested_urls.append(url)
        return self.pages[url]


def test_catalog_scraper_uses_injected_scraper():
    page_1_url = "https://example.com/"
    page_2_url = "https://example.com/page-2.html"

    page_1 = """
    <html>
    <body>
        <article class="product_pod">
            <h3>
                <a href="book-a.html" title="Book A">
                    Book A
                </a>
            </h3>

            <p class="price_color">£10.00</p>
            <p class="availability">In stock</p>
        </article>

        <li class="next">
            <a href="page-2.html">Next</a>
        </li>
    </body>
    </html>
    """

    page_2 = """
    <html>
    <body>
        <article class="product_pod">
            <h3>
                <a href="book-b.html" title="Book B">
                    Book B
                </a>
            </h3>

            <p class="price_color">£20.00</p>
            <p class="availability">In stock</p>
        </article>
    </body>
    </html>
    """

    fake_scraper = FakeScraper({
        page_1_url: page_1,
        page_2_url: page_2
    })

    catalog = CatalogScraper(
        BOOKS_TO_SCRAPE_CONFIG,
        scraper=fake_scraper
    )

    products = catalog.scrape_all(page_1_url)

    assert len(products) == 2

    assert products[0]["name"] == "Book A"
    assert products[1]["name"] == "Book B"

    assert fake_scraper.requested_urls == [
        page_1_url,
        page_2_url
    ]