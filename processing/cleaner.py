import re

import pandas as pd


class ProductCleaner:
    def __init__(
        self,
        available_keywords=None,
        unavailable_keywords=None
    ):
        self.available_keywords = (
            available_keywords
            if available_keywords is not None
            else (
                "in stock",
                "available",
                "left",
                "ready to ship"
            )
        )

        self.unavailable_keywords = (
            unavailable_keywords
            if unavailable_keywords is not None
            else (
                "out of stock",
                "sold out",
                "sold",
                "reserved",
                "unavailable",
                "not available",
                "0 available"
            )
        )

    def clean(self, products):
        df = pd.DataFrame(products)

        if df.empty:
            return df

        df["name"] = (
            df["name"]
            .astype(str)
            .str.strip()
        )

        df["price"] = df["price"].apply(
            self._parse_price
        )

        df["availability"] = (
            df["availability"].apply(
                self._parse_availability
            )
        )

        df["url"] = (
            df["url"]
            .astype(str)
            .str.strip()
        )

        df = df.drop_duplicates(
            subset=["url"]
        )

        return df

    def _parse_price(self, value):
        text = str(value).strip()

        cleaned = re.sub(
            r"[^\d,.\-]",
            "",
            text
        )

        if not cleaned:
            raise ValueError(
                f"Could not parse price: {value}"
            )

        comma_count = cleaned.count(",")
        dot_count = cleaned.count(".")

        # Example:
        # 1,299.99
        # 1.299,99
        if comma_count and dot_count:
            if cleaned.rfind(",") > cleaned.rfind("."):
                cleaned = cleaned.replace(".", "")
                cleaned = cleaned.replace(",", ".")
            else:
                cleaned = cleaned.replace(",", "")

        # Example:
        # 79,95
        # 1,299
        elif comma_count:
            cleaned = self._normalize_single_separator(
                cleaned,
                ","
            )

        # Example:
        # 79.95
        # 1.299
        elif dot_count:
            cleaned = self._normalize_single_separator(
                cleaned,
                "."
            )

        return float(cleaned)

    def _normalize_single_separator(
        self,
        value,
        separator
    ):
        parts = value.split(separator)

        # Multiple separators:
        # 1,234,567
        if len(parts) > 2:
            if all(
                len(part) == 3
                for part in parts[1:]
            ):
                return "".join(parts)

            decimal_part = parts[-1]

            whole_part = "".join(
                parts[:-1]
            )

            return (
                whole_part
                + "."
                + decimal_part
            )

        whole_part, decimal_part = parts

        # 1,299 or 1.299
        # Treat 3 trailing digits as thousands.
        if (
            len(decimal_part) == 3
            and whole_part
        ):
            return whole_part + decimal_part

        # 79,95 or 79.95
        return (
            whole_part
            + "."
            + decimal_part
        )

    def _parse_availability(self, value):
        if isinstance(value, bool):
            return value

        text = str(value).strip().lower()

        # Check unavailable FIRST.
        #
        # "not available" contains "available",
        # so checking True keywords first would
        # incorrectly classify it.
        for keyword in self.unavailable_keywords:
            if keyword in text:
                return False

        for keyword in self.available_keywords:
            if keyword in text:
                return True

        return False