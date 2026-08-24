from io import BytesIO
import pandas as pd


class DataExporter:
    def to_csv(self, df):
        return df.to_csv(index=False).encode("utf-8")

    def to_excel(self, df):
        buffer = BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine="openpyxl"
        ) as writer:
            df.to_excel(
                writer,
                index=False,
                sheet_name="Products"
            )

        buffer.seek(0)

        return buffer.getvalue()