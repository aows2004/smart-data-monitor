import threading

from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer
)

import pytest

from scraper.requests_scraper import RequestsScraper


class RetryTestHandler(BaseHTTPRequestHandler):
    request_count = 0

    def do_GET(self):
        type(self).request_count += 1

        if type(self).request_count < 3:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(
                b"Temporary failure"
            )
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"<html>Success</html>"
            )

    def log_message(self, format, *args):
        pass


def test_retries_temporary_server_errors():
    RetryTestHandler.request_count = 0

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        RetryTestHandler
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )

    thread.start()

    try:
        host, port = server.server_address

        url = f"http://{host}:{port}/"

        scraper = RequestsScraper(
            retries=2,
            backoff_factor=0
        )

        html = scraper.fetch_page(url)

        assert "Success" in html
        assert RetryTestHandler.request_count == 3

    finally:
        server.shutdown()
        server.server_close()
class NotFoundHandler(BaseHTTPRequestHandler):
    request_count = 0

    def do_GET(self):
        type(self).request_count += 1

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass

def test_does_not_retry_404():
    NotFoundHandler.request_count = 0

    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        NotFoundHandler
    )

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )

    thread.start()

    try:
        host, port = server.server_address

        url = f"http://{host}:{port}/missing"

        scraper = RequestsScraper(
            retries=3,
            backoff_factor=0
        )

        with pytest.raises(RuntimeError):
            scraper.fetch_page(url)

        assert NotFoundHandler.request_count == 1

    finally:
        server.shutdown()
        server.server_close()