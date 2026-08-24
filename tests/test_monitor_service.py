from config import BOOKS_TO_SCRAPE_CONFIG
from services.monitor_service import MonitorService
from storage.database import DatabaseManager


class FakeScraper:
    def __init__(self, pages):
        self.pages = pages

    def fetch_page(self, url):
        return self.pages[url]


def test_monitor_service_full_pipeline(tmp_path):
    source_url = "https://example.com/"

    first_html = """
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

    first_service = MonitorService(
        config=BOOKS_TO_SCRAPE_CONFIG,
        scraper=FakeScraper({
            source_url: first_html
        }),
        db_path=tmp_path / "monitor.db"
    )

    first_result = first_service.run(
        source_url
    )

    assert len(first_result["products"]) == 2

    assert len(first_result["new"]) == 2
    assert len(first_result["removed"]) == 0
    assert len(first_result["changed"]) == 0

    second_html = """
    <html>
    <body>

        <article class="product_pod">
            <h3>
                <a href="book-a.html" title="Book A">
                    Book A
                </a>
            </h3>

            <p class="price_color">£15.00</p>
            <p class="availability">In stock</p>
        </article>

        <article class="product_pod">
            <h3>
                <a href="book-c.html" title="Book C">
                    Book C
                </a>
            </h3>

            <p class="price_color">£30.00</p>
            <p class="availability">In stock</p>
        </article>

    </body>
    </html>
    """

    second_service = MonitorService(
        config=BOOKS_TO_SCRAPE_CONFIG,
        scraper=FakeScraper({
            source_url: second_html
        }),
        db_path=tmp_path / "monitor.db"
    )

    second_result = second_service.run(
        source_url
    )

    assert len(second_result["products"]) == 2

    assert len(second_result["new"]) == 1
    assert len(second_result["removed"]) == 1
    assert len(second_result["changed"]) == 1

    assert (
        second_result["new"].iloc[0]["name"]
        == "Book C"
    )

    assert (
        second_result["removed"].iloc[0]["name"]
        == "Book B"
    )

    changed = second_result["changed"].iloc[0]

    assert changed["old_price"] == 10.0
    assert changed["new_price"] == 15.0

def test_monitor_service_keeps_monitor_history_separate(
    tmp_path
):
    source_url = "https://example.com/"
    db_path = tmp_path / "monitors.db"

    first_html = """
    <html>
    <body>
        <article class="product_pod">
            <h3>
                <a href="a.html" title="Product A">
                    Product A
                </a>
            </h3>

            <p class="price_color">£10.00</p>
            <p class="availability">In stock</p>
        </article>
    </body>
    </html>
    """

    second_html = """
    <html>
    <body>
        <article class="product_pod">
            <h3>
                <a href="b.html" title="Product B">
                    Product B
                </a>
            </h3>

            <p class="price_color">£20.00</p>
            <p class="availability">In stock</p>
        </article>
    </body>
    </html>
    """

    database = DatabaseManager(
        db_path
    )

    monitor_1 = database.save_monitor(
        name="Monitor One",
        source_url=source_url,
        config=BOOKS_TO_SCRAPE_CONFIG,
        mode="Standard",
        max_pages=1
    )

    monitor_2 = database.save_monitor(
        name="Monitor Two",
        source_url=source_url,
        config=BOOKS_TO_SCRAPE_CONFIG,
        mode="Standard",
        max_pages=2
    )

    service_1 = MonitorService(
        config=BOOKS_TO_SCRAPE_CONFIG,
        scraper=FakeScraper({
            source_url: first_html
        }),
        db_path=db_path,
        max_pages=1,
        monitor_id=monitor_1
    )

    service_2 = MonitorService(
        config=BOOKS_TO_SCRAPE_CONFIG,
        scraper=FakeScraper({
            source_url: second_html
        }),
        db_path=db_path,
        max_pages=2,
        monitor_id=monitor_2
    )

    result_1 = service_1.run(
        source_url
    )

    result_2 = service_2.run(
        source_url
    )

    assert len(result_1["new"]) == 1
    assert len(result_2["new"]) == 1

    second_result_1 = service_1.run(
        source_url
    )

    assert len(
        second_result_1["new"]
    ) == 0

    assert (
        second_result_1["products"]
        .iloc[0]["name"]
        == "Product A"
    )