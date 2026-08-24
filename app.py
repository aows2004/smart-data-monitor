from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from config import (
    BOOKS_TO_SCRAPE_CONFIG,
    ScrapeConfig
)
from exporters.exporter import DataExporter
from processing.validator import ScrapeValidationError
from scraper.playwright_scraper import PlaywrightScraper
from services.monitor_service import MonitorService
from storage.database import DatabaseManager


# --------------------------------------------------
# Constants
# --------------------------------------------------

DB_PATH = "data/smartdata.db"


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="SmartData Monitor",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# Database
# --------------------------------------------------

database = DatabaseManager(DB_PATH)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def is_valid_http_url(value):
    try:
        parsed = urlparse(value)

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )

    except ValueError:
        return False


def optional_text(value):
    if value is None:
        return None

    if pd.isna(value):
        return None

    value = str(value).strip()

    return value or None


def show_dataframe(df):
    if df.empty:
        return

    column_config = {}

    if "price" in df.columns:
        column_config["price"] = (
            st.column_config.NumberColumn(
                "Price",
                format="%.2f"
            )
        )

    if "availability" in df.columns:
        column_config["availability"] = (
            st.column_config.CheckboxColumn(
                "Available"
            )
        )

    if "url" in df.columns:
        column_config["url"] = (
            st.column_config.LinkColumn(
                "Product",
                display_text="Open product",
                width="medium"
            )
        )

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
        column_config=column_config
    )
def format_history(df):
    if df.empty:
        return df

    formatted = df.copy()

    if "scraped_at" in formatted.columns:
        formatted["scraped_at"] = (
            pd.to_datetime(
                formatted["scraped_at"],
                utc=True
            )
            .dt.strftime(
                "%Y-%m-%d %H:%M UTC"
            )
        )

        formatted = formatted.rename(
            columns={
                "scraped_at": "Run Time",
                "product_count": "Products",
                "source_url": "Source",
                "id": "Run ID"
            }
        )

    return formatted


def build_config_from_monitor(monitor):
    return ScrapeConfig(
        product_selector=monitor[
            "product_selector"
        ],
        name_selector=monitor[
            "name_selector"
        ],
        price_selector=monitor[
            "price_selector"
        ],
        availability_selector=optional_text(
            monitor["availability_selector"]
        ),
        link_selector=monitor[
            "link_selector"
        ],
        next_page_selector=optional_text(
            monitor["next_page_selector"]
        ),
        name_attribute=optional_text(
            monitor["name_attribute"]
        ),
        link_attribute=monitor[
            "link_attribute"
        ]
    )


def execute_monitor(
    config,
    source_url,
    mode,
    max_pages,
    monitor_id,
    configuration_label
):
    scraper = None

    if mode == "Dynamic / JavaScript":
        scraper = PlaywrightScraper(
            wait_for_selector=(
                config.product_selector
            )
        )

    service = MonitorService(
        config=config,
        scraper=scraper,
        db_path=DB_PATH,
        max_pages=int(max_pages),
        monitor_id=monitor_id
    )

    try:
        with st.spinner(
            "Scraping, cleaning, validating, "
            "and comparing data..."
        ):
            result = service.run(
                source_url
            )

            result["history"] = (
                service.database.get_run_history(
                    source_url=source_url,
                    monitor_id=monitor_id
                )
            )

        st.session_state.monitor_result = (
            result
        )

        st.session_state.last_source_url = (
            source_url
        )

        st.session_state.last_mode = mode

        st.session_state.last_configuration = (
            configuration_label
        )

        st.session_state.last_monitor_id = (
            monitor_id
        )

        st.success(
            "Monitoring run completed successfully."
        )

    except ScrapeValidationError as error:
        st.error(
            f"Scrape validation failed: {error}"
        )

    except ValueError as error:
        st.error(
            f"Data normalization failed: {error}"
        )

    except RuntimeError as error:
        st.error(
            f"Scraping failed: {error}"
        )

    except Exception as error:
        st.error(
            f"Unexpected error: {error}"
        )


# --------------------------------------------------
# Session state
# --------------------------------------------------

if "monitor_result" not in st.session_state:
    st.session_state.monitor_result = None

if "last_source_url" not in st.session_state:
    st.session_state.last_source_url = None

if "last_mode" not in st.session_state:
    st.session_state.last_mode = None

if "last_configuration" not in st.session_state:
    st.session_state.last_configuration = None

if "last_monitor_id" not in st.session_state:
    st.session_state.last_monitor_id = None


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("📊 SmartData Monitor")

st.write(
    "Track product listings across websites, "
    "detect price and availability changes, "
    "and maintain historical snapshots."
)

st.divider()


# --------------------------------------------------
# Monitor source
# --------------------------------------------------

st.subheader("Monitor Configuration")

monitor_source = st.radio(
    "Choose how to monitor",
    [
        "New configuration",
        "Saved monitor"
    ],
    horizontal=True
)


# ==================================================
# NEW CONFIGURATION
# ==================================================

if monitor_source == "New configuration":

    site_type = st.selectbox(
        "Website configuration",
        [
            "Books to Scrape preset",
            "Custom website"
        ]
    )

    with st.form("new_monitor_form"):

        st.markdown("#### Monitor Profile")

        monitor_name = st.text_input(
            "Monitor name",
            placeholder=(
                "Example: Competitor Store"
            )
        )

        save_profile = st.checkbox(
            "Save this configuration as a monitor",
            value=True
        )

        st.markdown("#### Website")

        # ------------------------------------------
        # Preset
        # ------------------------------------------

        if site_type == (
            "Books to Scrape preset"
        ):

            url = st.text_input(
                "Website URL",
                value=(
                    "https://books.toscrape.com/"
                )
            )

            st.caption(
                "CSS selectors are automatically "
                "configured for this demo site."
            )

            product_selector = None
            name_selector = None
            price_selector = None
            availability_selector = None
            link_selector = None
            next_page_selector = None
            name_attribute = None
            link_attribute = None

        # ------------------------------------------
        # Custom
        # ------------------------------------------

        else:

            url = st.text_input(
                "Website URL",
                placeholder=(
                    "https://example.com/"
                )
            )

            st.markdown(
                "#### CSS Selectors"
            )

            column_1, column_2 = (
                st.columns(2)
            )

            with column_1:

                product_selector = (
                    st.text_input(
                        "Product card selector",
                        placeholder=(
                            ".product-card"
                        )
                    )
                )

                name_selector = (
                    st.text_input(
                        "Name selector",
                        placeholder=(
                            ".product-title"
                        )
                    )
                )

                price_selector = (
                    st.text_input(
                        "Price selector",
                        placeholder=".price"
                    )
                )

                availability_selector = (
                    st.text_input(
                        "Availability selector",
                        placeholder=(
                            ".stock-status"
                        )
                    )
                )

            with column_2:

                link_selector = (
                    st.text_input(
                        "Product link selector",
                        placeholder=(
                            "a.product-link"
                        )
                    )
                )

                next_page_selector = (
                    st.text_input(
                        "Next-page selector "
                        "(optional)",
                        placeholder=(
                            ".pagination .next"
                        )
                    )
                )

                name_attribute = (
                    st.text_input(
                        "Name attribute "
                        "(optional)",
                        placeholder="title"
                    )
                )

                link_attribute = (
                    st.text_input(
                        "Link attribute",
                        value="href"
                    )
                )

        # ------------------------------------------
        # Scraping options
        # ------------------------------------------

        st.markdown(
            "#### Scraping Options"
        )

        option_1, option_2 = (
            st.columns(2)
        )

        with option_1:

            mode = st.selectbox(
                "Scraping mode",
                [
                    "Standard",
                    "Dynamic / JavaScript"
                ]
            )

        with option_2:

            max_pages = st.number_input(
                "Maximum pages",
                min_value=1,
                max_value=100,
                value=2,
                step=1
            )

        submitted = st.form_submit_button(
            "Run Monitor",
            type="primary",
            width="stretch"
        )

    # ----------------------------------------------
    # Handle new monitor submission
    # ----------------------------------------------

    if submitted:

        source_url = url.strip()

        errors = []

        if not source_url:
            errors.append(
                "Website URL is required."
            )

        elif not is_valid_http_url(
            source_url
        ):
            errors.append(
                "Website URL must be a valid "
                "HTTP or HTTPS URL."
            )

        if save_profile:
            if not monitor_name.strip():
                errors.append(
                    "Monitor name is required "
                    "when saving a profile."
                )

        if site_type == "Custom website":

            required_fields = {
                "Product card selector":
                    product_selector,

                "Name selector":
                    name_selector,

                "Price selector":
                    price_selector,

                "Availability selector":
                    availability_selector,

                "Product link selector":
                    link_selector,

                "Link attribute":
                    link_attribute
            }

            for field_name, value in (
                required_fields.items()
            ):
                if not value.strip():
                    errors.append(
                        f"{field_name} is required."
                    )

        if errors:

            st.error(
                "\n".join(
                    f"• {error}"
                    for error in errors
                )
            )

        else:

            if site_type == (
                "Books to Scrape preset"
            ):

                config = (
                    BOOKS_TO_SCRAPE_CONFIG
                )

            else:

                config = ScrapeConfig(
                    product_selector=(
                        product_selector.strip()
                    ),

                    name_selector=(
                        name_selector.strip()
                    ),

                    price_selector=(
                        price_selector.strip()
                    ),

                    availability_selector=(
                        availability_selector.strip()
                    ),

                    link_selector=(
                        link_selector.strip()
                    ),

                    next_page_selector=(
                        next_page_selector.strip()
                        or None
                    ),

                    name_attribute=(
                        name_attribute.strip()
                        or None
                    ),

                    link_attribute=(
                        link_attribute.strip()
                    )
                )

            monitor_id = None

            if save_profile:

                monitor_id = (
                    database.save_monitor(
                        name=(
                            monitor_name.strip()
                        ),
                        source_url=source_url,
                        config=config,
                        mode=mode,
                        max_pages=max_pages
                    )
                )

                configuration_label = (
                    monitor_name.strip()
                )

            else:

                configuration_label = (
                    site_type
                )

            execute_monitor(
                config=config,
                source_url=source_url,
                mode=mode,
                max_pages=max_pages,
                monitor_id=monitor_id,
                configuration_label=(
                    configuration_label
                )
            )


# ==================================================
# SAVED MONITOR
# ==================================================

else:

    monitors = database.list_monitors()

    if monitors.empty:

        st.info(
            "No saved monitors yet. "
            "Create one using New configuration."
        )

    else:

        monitor_ids = [
            int(value)
            for value
            in monitors["id"].tolist()
        ]

        labels = {}

        for _, row in monitors.iterrows():

            monitor_id = int(
                row["id"]
            )

            labels[monitor_id] = (
                f"{row['name']} — "
                f"{row['source_url']}"
            )

        selected_monitor_id = st.selectbox(
            "Saved monitor",
            options=monitor_ids,
            format_func=lambda value: (
                labels[value]
            )
        )

        monitor = database.load_monitor(
            selected_monitor_id
        )

        if monitor is not None:

            st.markdown(
                f"### {monitor['name']}"
            )

            info_1, info_2, info_3 = (
                st.columns(3)
            )

            with info_1:
                st.metric(
                    "Mode",
                    monitor["mode"],
                    border=True
                )

            with info_2:
                st.metric(
                    "Max Pages",
                    int(
                        monitor["max_pages"]
                    ),
                    border=True
                )

            with info_3:
                st.metric(
                    "Monitor ID",
                    int(
                        monitor["id"]
                    ),
                    border=True
                )

            st.write(
                f"**Website:** "
                f"{monitor['source_url']}"
            )

            with st.expander(
                "View CSS selectors"
            ):

                st.code(
                    "\n".join([
                        "Product: "
                        + monitor[
                            "product_selector"
                        ],

                        "Name: "
                        + monitor[
                            "name_selector"
                        ],

                        "Price: "
                        + monitor[
                            "price_selector"
                        ],

                        "Availability: "
                        + str(
                            optional_text(
                                monitor[
                                    "availability_selector"
                                ]
                            )
                        ),

                        "Link: "
                        + monitor[
                            "link_selector"
                        ],

                        "Next page: "
                        + str(
                            optional_text(
                                monitor[
                                    "next_page_selector"
                                ]
                            )
                        )
                    ])
                )

            run_saved = st.button(
                "Run Saved Monitor",
                type="primary",
                width="stretch"
            )

            if run_saved:

                config = (
                    build_config_from_monitor(
                        monitor
                    )
                )

                execute_monitor(
                    config=config,

                    source_url=monitor[
                        "source_url"
                    ],

                    mode=monitor[
                        "mode"
                    ],

                    max_pages=int(
                        monitor[
                            "max_pages"
                        ]
                    ),

                    monitor_id=int(
                        monitor["id"]
                    ),

                    configuration_label=(
                        monitor["name"]
                    )
                )


# ==================================================
# RESULTS
# ==================================================

result = st.session_state.monitor_result

if result is not None:

    st.divider()

    st.subheader(
        "Monitoring Results"
    )

    st.caption(
    f"{st.session_state.last_configuration}"
    f" • {st.session_state.last_mode}"
    f" • {st.session_state.last_source_url}"
)

with st.expander("Run details"):
    st.write(
        f"**Run ID:** {result['run_id']}"
    )

    if (
        st.session_state.last_monitor_id
        is not None
    ):
        st.write(
            "**Monitor ID:** "
            f"{st.session_state.last_monitor_id}"
        )

    products = result["products"]
    new_products = result["new"]
    changed_products = result["changed"]
    removed_products = result["removed"]

    metric_1, metric_2, metric_3, metric_4 = (
        st.columns(4)
    )

    with metric_1:
        st.metric(
            "Products",
            len(products),
            border=True
        )

    with metric_2:
        st.metric(
            "New",
            len(new_products),
            border=True
        )

    with metric_3:
        st.metric(
            "Changed",
            len(changed_products),
            border=True
        )

    with metric_4:
        st.metric(
            "Removed",
            len(removed_products),
            border=True
        )
    total_changes = (
      len(new_products)
    + len(changed_products)
    + len(removed_products)
    )

if total_changes == 0:
    st.success(
        "No changes detected since the previous run."
    )

else:
    st.warning(
        f"{total_changes} change(s) detected "
        "since the previous run."
    )
    st.divider()

    (
        products_tab,
        new_tab,
        changed_tab,
        removed_tab,
        history_tab
    ) = st.tabs(
        [
            "Products",
            "New",
            "Changed",
            "Removed",
            "Run History"
        ]
    )

    with products_tab:

        st.subheader(
            "Current Products"
        )

        if products.empty:
            st.info(
                "No products found."
            )
        else:
            show_dataframe(products)

    with new_tab:

        st.subheader(
            "New Products"
        )

        if new_products.empty:
            st.info(
                "No new products detected."
            )
        else:
            show_dataframe(
                new_products
            )

    with changed_tab:

        st.subheader(
            "Changed Products"
        )

        if changed_products.empty:
            st.info(
                "No product changes detected."
            )
        else:
            show_dataframe(
                changed_products
            )

    with removed_tab:

        st.subheader(
            "Removed Products"
        )

        if removed_products.empty:
            st.info(
                "No removed products detected."
            )
        else:
            show_dataframe(
                removed_products
            )

    with history_tab:

        st.subheader(
            "Run History"
        )

        history = result["history"]

        if history.empty:
            st.info(
                "No historical runs available."
            )
        else:
            st.dataframe(
                format_history(history),
                width="stretch",
                hide_index=True
            )

    # ----------------------------------------------
    # Exports
    # ----------------------------------------------

    st.divider()

    st.subheader(
        "Export Current Snapshot"
    )

    exporter = DataExporter()

    csv_data = exporter.to_csv(
        products
    )

    excel_data = exporter.to_excel(
        products
    )

    export_1, export_2 = (
        st.columns(2)
    )

    with export_1:

        st.download_button(
            "Download CSV",
            data=csv_data,
            file_name=(
                "smartdata_products.csv"
            ),
            mime="text/csv",
            width="stretch"
        )

    with export_2:

        st.download_button(
            "Download Excel",
            data=excel_data,
            file_name=(
                "smartdata_products.xlsx"
            ),
            mime=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            width="stretch"
        )