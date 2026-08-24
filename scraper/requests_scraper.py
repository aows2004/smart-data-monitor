import requests
from requests.exceptions import RequestException
from utils.logger import get_logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class RequestsScraper:
    def __init__(
    self,
    timeout=10,
    retries=3,
    backoff_factor=0.5
):
        self.timeout = timeout
        self.logger = get_logger(self.__class__.__name__)

        self.session = requests.Session()

        retry_strategy = Retry(
            total=retries,
            connect=retries,
            read=retries,
            status=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504
            ],
            allowed_methods=frozenset(["GET"]),
            respect_retry_after_header=True
            )

        adapter = HTTPAdapter(
        max_retries=retry_strategy
        )

        self.session.mount(
        "http://",
        adapter
        )

        self.session.mount(
        "https://",
        adapter
        )

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/149.0.0.0 Safari/537.36"
            )
        })
    def fetch_page(self, url):
        try:
            response = self.session.get(
                url,
                timeout=self.timeout
            )

            response.raise_for_status()
            response.encoding= response.apparent_encoding
            return response.text

        except RequestException as error:
            self.logger.error(
                "Failed to fetch %s: %s",
                url,
                error
            )

            raise RuntimeError(
                f"Failed to fetch '{url}': {error}"
            ) from error
    def close(self):
        self.session.close()