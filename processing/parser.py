from urllib.parse import urljoin

from bs4 import BeautifulSoup

from config import ScrapeConfig


class ProductParser:
    def __init__(self, config: ScrapeConfig):
        self.config = config

    def parse(self, html, page_url):
        soup = BeautifulSoup(html, "html.parser")

        products = []

        product_cards = soup.select(
            self.config.product_selector
        )

        for card in product_cards:
            name_tag = card.select_one(
                self.config.name_selector
            )

            price_tag = card.select_one(
                self.config.price_selector
            )

            availability_tag = None

            if self.config.availability_selector:
                availability_tag = card.select_one(
                    self.config.availability_selector
                )

            link_tag = card.select_one(
                self.config.link_selector
            )

            if (
                name_tag is None
                or price_tag is None
                or link_tag is None
            ):
                continue

            if self.config.name_attribute:
                name = name_tag.get(
                    self.config.name_attribute,
                    ""
                ).strip()
            else:
                name = name_tag.get_text(
                    " ",
                    strip=True
                )

            product = {
                "name": name,

                "price": price_tag.get_text(
                    strip=True
                ),

                "availability": (
                    availability_tag.get_text(
                        " ",
                        strip=True
                    )
                    if availability_tag
                    else "Unknown"
                ),

                "url": urljoin(
                    page_url,
                    link_tag.get(
                        self.config.link_attribute,
                        ""
                    )
                )
            }

            products.append(product)

        return products

    def get_next_page_url(self, html, page_url):
        if not self.config.next_page_selector:
            return None
        soup = BeautifulSoup(html, "html.parser")

        next_link = soup.select_one(
            self.config.next_page_selector
        )

        if next_link is None:
            return None

        href = next_link.get("href")

        if not href:
            return None

        return urljoin(page_url, href)