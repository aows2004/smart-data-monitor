from processing.cleaner import ProductCleaner
from processing.comparator import ProductComparator
from processing.validator import ScrapeValidator
from scraper.catalog_scraper import CatalogScraper
from storage.database import DatabaseManager


class MonitorService:
    def __init__(
        self,
        config,
        scraper=None,
        db_path="data/smartdata.db",
        max_pages=100,
        validator=None,
        monitor_id=None
    ):
        self.catalog = CatalogScraper(
            config=config,
            scraper=scraper,
            max_pages=max_pages
    )

        self.cleaner = ProductCleaner()
        self.comparator = ProductComparator()

        self.validator = (
            validator
            if validator is not None
            else ScrapeValidator()
    )

        self.database = DatabaseManager(
            db_path
        )

        self.monitor_id = monitor_id

    def run(self, source_url):
        previous_df = (
            self.database.load_latest_snapshot(
                source_url= source_url,
                monitor_id=self.monitor_id
            )
        )

        raw_products = self.catalog.scrape_all(
            source_url
        )

        current_df = self.cleaner.clean(
            raw_products
        )

        self.validator.validate(
            current_df,
            previous_df
        )

        changes = self.comparator.compare(
            previous_df,
            current_df
        )

        run_id = self.database.save_snapshot(
            current_df,
            source_url,
            monitor_id=self.monitor_id
        )

        return {
            "run_id": run_id,
            "products": current_df,
            "previous_products": previous_df,
            "new": changes["new"],
            "removed": changes["removed"],
            "changed": changes["changed"]
        }