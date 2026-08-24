from scraper.requests_scraper import RequestsScraper
from processing.parser import ProductParser
from utils.logger import get_logger
from config import ScrapeConfig


class CatalogScraper:
    def __init__(self, config: ScrapeConfig,scraper=None, max_pages=100):
        self.scraper = (
            scraper
            if scraper is not None
            else RequestsScraper()
            )

        self.parser = ProductParser(config)
        self.max_pages = max_pages
        self.logger = get_logger(self.__class__.__name__)

    def scrape_all(self, start_url):
        products = []
        current_url = start_url
        visited_urls = set()
        pages_scraped = 0

        start_method = getattr(
            self.scraper,
            "start",
            None
            )

        close_method = getattr(
            self.scraper,
            "close",
            None
        )

        if callable(start_method):
            start_method()

        try:
            while current_url is not None:
                if current_url in visited_urls:
                    self.logger.warning(
                        "Pagination loop detected at %s",
                        current_url
                        )
                    break

                if pages_scraped >= self.max_pages:
                    self.logger.warning(
                        "Maximum page limit reached: %s",
                        self.max_pages
                    )
                    break

                visited_urls.add(current_url)

                html = self.scraper.fetch_page(
                    current_url
                )

                page_products = self.parser.parse(
                    html,
                    current_url
                )

                products.extend(page_products)

                pages_scraped += 1

                self.logger.info(
                    "Scraped page %s: %s products",
                    pages_scraped,
                    len(page_products)
                    )

                current_url = (
                    self.parser.get_next_page_url(
                        html,
                        current_url
                    )
                )

            return products

        finally:
            if callable(close_method):
                close_method()