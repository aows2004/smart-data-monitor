import pandas as pd

from storage.database import DatabaseManager

from config import BOOKS_TO_SCRAPE_CONFIG


def test_save_and_load_snapshot(tmp_path):
    db_path = tmp_path / "test.db"

    db = DatabaseManager(db_path)

    original = pd.DataFrame([
        {
            "name": "Laptop A",
            "price": 850.0,
            "availability": True,
            "url": "https://shop/a"
        },
        {
            "name": "Laptop B",
            "price": 600.0,
            "availability": False,
            "url": "https://shop/b"
        }
    ])

    run_id = db.save_snapshot(
        original,
        "https://shop"
    )

    loaded = db.load_latest_snapshot(
        "https://shop"
    )

    assert run_id == 1
    assert len(loaded) == 2

    assert set(loaded["url"]) == {
        "https://shop/a",
        "https://shop/b"
    }

    assert loaded.iloc[0]["price"] == 850.0
    assert loaded["availability"].dtype == bool


def test_run_history(tmp_path):
    db_path = tmp_path / "test.db"

    db = DatabaseManager(db_path)

    df = pd.DataFrame([
        {
            "name": "Laptop A",
            "price": 850.0,
            "availability": True,
            "url": "https://shop/a"
        }
    ])

    db.save_snapshot(df, "https://shop")
    db.save_snapshot(df, "https://shop")

    history = db.get_run_history(
        "https://shop"
    )

    assert len(history) == 2

    assert history.iloc[0]["id"] == 2
    assert history.iloc[1]["id"] == 1

    assert history.iloc[0]["product_count"] == 1
def test_monitor_profile_can_be_saved_and_loaded(
    tmp_path
    ):
    database = DatabaseManager(
        tmp_path / "monitors.db"
    )

    monitor_id = database.save_monitor(
        name="Books Monitor",
        source_url="https://example.com/",
        config=BOOKS_TO_SCRAPE_CONFIG,
        mode="Standard",
        max_pages=2
    )

    monitor = database.load_monitor(
        monitor_id
    )

    assert monitor is not None
    assert monitor["name"] == "Books Monitor"

    assert (
        monitor["source_url"]
        == "https://example.com/"
    )

    assert monitor["mode"] == "Standard"
    assert monitor["max_pages"] == 2
def test_monitors_with_same_url_have_separate_history(
    tmp_path
):
    database = DatabaseManager(
        tmp_path / "isolated.db"
    )

    monitor_1 = database.save_monitor(
        name="Small Crawl",
        source_url="https://example.com/",
        config=BOOKS_TO_SCRAPE_CONFIG,
        mode="Standard",
        max_pages=2
    )

    monitor_2 = database.save_monitor(
        name="Large Crawl",
        source_url="https://example.com/",
        config=BOOKS_TO_SCRAPE_CONFIG,
        mode="Standard",
        max_pages=10
    )

    df_1 = pd.DataFrame([
        {
            "name": "Product A",
            "price": 10.0,
            "availability": True,
            "url": "https://example.com/a"
        }
    ])

    df_2 = pd.DataFrame([
        {
            "name": "Product B",
            "price": 20.0,
            "availability": True,
            "url": "https://example.com/b"
        }
    ])

    database.save_snapshot(
        df_1,
        "https://example.com/",
        monitor_id=monitor_1
    )

    database.save_snapshot(
        df_2,
        "https://example.com/",
        monitor_id=monitor_2
    )

    latest_1 = (
        database.load_latest_snapshot(
            monitor_id=monitor_1
        )
    )

    latest_2 = (
        database.load_latest_snapshot(
            monitor_id=monitor_2
        )
    )

    assert latest_1.iloc[0]["name"] == "Product A"
    assert latest_2.iloc[0]["name"] == "Product B"