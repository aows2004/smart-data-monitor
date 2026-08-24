from scraper.playwright_scraper import PlaywrightScraper


def test_renders_javascript_content(tmp_path):
    html_file = tmp_path / "dynamic.html"

    html_file.write_text(
        """
        <!DOCTYPE html>
        <html>
        <body>
            <div id="products"></div>

            <script>
                setTimeout(() => {
                    document.getElementById("products").innerHTML =
                        '<div class="product-card">JavaScript Product</div>';
                }, 100);
            </script>
        </body>
        </html>
        """,
        encoding="utf-8"
    )

    url = html_file.resolve().as_uri()

    with PlaywrightScraper(
        timeout=5_000,
        wait_for_selector=".product-card"
    ) as scraper:

        rendered_html = scraper.fetch_page(url)

    assert "JavaScript Product" in rendered_html
    assert 'class="product-card"' in rendered_html
def test_reuses_browser_for_multiple_pages(tmp_path):
    page_one = tmp_path / "page_one.html"
    page_two = tmp_path / "page_two.html"

    page_one.write_text(
        """
        <html>
        <body>
            <div class="ready">Page One</div>
        </body>
        </html>
        """,
        encoding="utf-8"
    )

    page_two.write_text(
        """
        <html>
        <body>
            <div class="ready">Page Two</div>
        </body>
        </html>
        """,
        encoding="utf-8"
    )

    scraper = PlaywrightScraper(
        timeout=5_000,
        wait_for_selector=".ready"
    )

    scraper.start()

    try:
        original_browser = scraper._browser
        original_context = scraper._context

        first_html = scraper.fetch_page(
            page_one.resolve().as_uri()
        )

        second_html = scraper.fetch_page(
            page_two.resolve().as_uri()
        )

        assert "Page One" in first_html
        assert "Page Two" in second_html

        assert scraper._browser is original_browser
        assert scraper._context is original_context

    finally:
        scraper.close()

    assert scraper._browser is None
    assert scraper._context is None
    assert scraper._page is None