class ScrapeValidationError(RuntimeError):
    pass


class ScrapeValidator:
    def __init__(
        self,
        minimum_products=1,
        maximum_drop_ratio=0.5
    ):
        self.minimum_products = minimum_products
        self.maximum_drop_ratio = maximum_drop_ratio

    def validate(self, new_df, previous_df=None):
        if len(new_df) < self.minimum_products:
            raise ScrapeValidationError(
                "Scrape returned too few products "
                f"({len(new_df)} found, "
                f"minimum expected: {self.minimum_products})."
            )

        required_columns = {
            "name",
            "price",
            "availability",
            "url"
        }

        missing_columns = (
            required_columns
            - set(new_df.columns)
        )

        if missing_columns:
            raise ScrapeValidationError(
                "Scraped data is missing required columns: "
                + ", ".join(sorted(missing_columns))
            )

        if (
            previous_df is not None
            and not previous_df.empty
        ):
            previous_count = len(previous_df)
            new_count = len(new_df)

            drop_ratio = (
                previous_count - new_count
            ) / previous_count

            if drop_ratio > self.maximum_drop_ratio:
                raise ScrapeValidationError(
                    "Suspicious product-count drop detected: "
                    f"{previous_count} -> {new_count} "
                    f"({drop_ratio:.1%} decrease)."
                )

        return True