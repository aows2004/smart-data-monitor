import pandas as pd


class ProductComparator:
    def compare(self, old_df, new_df):
        change_columns = [
            "url",
            "old_name",
            "new_name",
            "old_price",
            "new_price",
            "old_availability",
            "new_availability"
        ]

        if old_df.empty:
            return {
                "new": new_df.copy(),
                "removed": pd.DataFrame(),
                "changed": pd.DataFrame(columns=change_columns)
            }

        if new_df.empty:
            return {
                "new": pd.DataFrame(),
                "removed": old_df.copy(),
                "changed": pd.DataFrame(columns=change_columns)
            }

        old_indexed = old_df.set_index("url")
        new_indexed = new_df.set_index("url")

        new_urls = new_indexed.index.difference(old_indexed.index)
        removed_urls = old_indexed.index.difference(new_indexed.index)
        common_urls = old_indexed.index.intersection(new_indexed.index)

        new_products = new_indexed.loc[new_urls].reset_index()
        removed_products = old_indexed.loc[removed_urls].reset_index()

        changes = []

        for url in common_urls:
            old_product = old_indexed.loc[url]
            new_product = new_indexed.loc[url]

            if (
                old_product["name"] != new_product["name"]
                or old_product["price"] != new_product["price"]
                or old_product["availability"] != new_product["availability"]
            ):
             changes.append({
                "url": url,
                "old_name": old_product["name"],
                "new_name": new_product["name"],
                "old_price": old_product["price"],
                "new_price": new_product["price"],
                "old_availability": old_product["availability"],
                "new_availability": new_product["availability"]
            })

        changed_products = pd.DataFrame(
            changes,
            columns=change_columns
        )

        return {
            "new": new_products,
            "removed": removed_products,
            "changed": changed_products
        }