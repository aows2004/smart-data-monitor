from io import BytesIO

import pandas as pd

from exporters.exporter import DataExporter


def sample_dataframe():
    return pd.DataFrame([
        {
            "name": "Laptop A",
            "price": 850.0
        },
        {
            "name": "Laptop B",
            "price": 600.0
        }
    ])


def test_csv_export():
    df = sample_dataframe()

    csv_bytes = DataExporter().to_csv(df)

    csv_text = csv_bytes.decode("utf-8")

    assert "name,price" in csv_text
    assert "Laptop A,850.0" in csv_text
    assert "Laptop B,600.0" in csv_text


def test_excel_export():
    df = sample_dataframe()

    excel_bytes = DataExporter().to_excel(df)

    assert len(excel_bytes) > 0
    assert excel_bytes[:2] == b"PK"

    loaded = pd.read_excel(
        BytesIO(excel_bytes)
    )

    assert len(loaded) == 2
    assert loaded.iloc[0]["name"] == "Laptop A"
    assert loaded.iloc[0]["price"] == 850