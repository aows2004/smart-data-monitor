from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapeConfig:
    product_selector: str
    name_selector: str
    price_selector: str
    link_selector: str

    availability_selector: str | None = None
    next_page_selector: str | None = None

    name_attribute: str | None = None
    link_attribute: str = "href"


BOOKS_TO_SCRAPE_CONFIG = ScrapeConfig(
    product_selector="article.product_pod",
    name_selector="h3 a",
    price_selector=".price_color",
    availability_selector=".availability",
    link_selector="h3 a",
    next_page_selector="li.next a",
    name_attribute="title"
)