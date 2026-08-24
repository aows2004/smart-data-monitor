from playwright.sync_api import (
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright
)

from utils.logger import get_logger


class PlaywrightScraper:
    def __init__(
        self,
        timeout=30_000,
        headless=True,
        wait_for_selector=None
    ):
        self.timeout = timeout
        self.headless = headless
        self.wait_for_selector = wait_for_selector

        self.logger = get_logger(
            self.__class__.__name__
        )

        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    def start(self):
        if self._playwright is not None:
            return self

        try:
            self._playwright = sync_playwright().start()

            self._browser = (
                self._playwright.chromium.launch(
                    headless=self.headless
                )
            )

            self._context = self._browser.new_context()

            self._page = self._context.new_page()

            return self

        except PlaywrightError as error:
            self.close()

            raise RuntimeError(
                f"Failed to start browser: {error}"
            ) from error

    def close(self):
        try:
            if self._context is not None:
                self._context.close()

        finally:
            try:
                if self._browser is not None:
                    self._browser.close()

            finally:
                if self._playwright is not None:
                    self._playwright.stop()

                self._page = None
                self._context = None
                self._browser = None
                self._playwright = None

    def __enter__(self):
        return self.start()

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback
    ):
        self.close()

    def fetch_page(self, url):
        self.start()

        try:
            self._page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.timeout
            )

            if self.wait_for_selector:
                self._page.locator(
                    self.wait_for_selector
                ).first.wait_for(
                    state="attached",
                    timeout=self.timeout
                )

            return self._page.content()

        except PlaywrightTimeoutError as error:
            self.logger.error(
                "Timed out loading %s: %s",
                url,
                error
            )

            raise RuntimeError(
                f"Timed out loading '{url}'"
            ) from error

        except PlaywrightError as error:
            self.logger.error(
                "Browser failed for %s: %s",
                url,
                error
            )

            raise RuntimeError(
                f"Browser failed for '{url}': {error}"
            ) from error