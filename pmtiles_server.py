#!/usr/bin/env python3
"""
PMTiles server with HTTP Range Request support.
Serves PMTiles archives efficiently by supporting Range requests.
"""

import http.server
import os
import mimetypes
import sys
from urllib.parse import unquote, urlparse


class PMTilesHTTPServer(http.server.HTTPServer):
    """HTTP server that can serve either a directory or a single file."""

    def __init__(self, server_address, handler, root_path):
        super().__init__(server_address, handler)
        self.root_path = os.path.abspath(root_path)


class RangeRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler with Range request support for efficient file serving."""

    def do_GET(self):
        self._handle_request("GET")

    def do_HEAD(self):
        self._handle_request("HEAD")

    def do_OPTIONS(self):
        self._send_cors_headers(204, None)
        self.end_headers()

    def _handle_request(self, method):
        if self.path == "*":
            self.send_error(400, "Bad Request")
            return

        full_path = self._resolve_path()
        if full_path is None:
            self.send_error(404, "File not found")
            return

        try:
            file_size = os.path.getsize(full_path)
        except OSError:
            self.send_error(404, "File not found")
            return

        range_header = self.headers.get("Range")

        if range_header:
            try:
                if not range_header.startswith("bytes="):
                    self.send_error(416, "Range Not Satisfiable")
                    return

                ranges_str = range_header[6:]
                ranges = []
                for range_spec in ranges_str.split(","):
                    range_spec = range_spec.strip()
                    if "-" not in range_spec:
                        self.send_error(416, "Range Not Satisfiable")
                        return

                    start_str, end_str = range_spec.split("-", 1)
                    if start_str == "":
                        suffix_length = int(end_str)
                        start = max(0, file_size - suffix_length)
                        end = file_size - 1
                    else:
                        start = int(start_str)
                        end = int(end_str) if end_str else file_size - 1

                    if start < 0 or end >= file_size or start > end:
                        self.send_error(416, "Range Not Satisfiable")
                        return

                    ranges.append((start, end))

                if len(ranges) > 1:
                    self.send_error(416, "Range Not Satisfiable")
                    return

                start, end = ranges[0]
                content_length = end - start + 1
                self._send_cors_headers(206, full_path, content_range=f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Type", self._guess_type(full_path))
                self.send_header("Content-Length", str(content_length))
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                if method == "GET":
                    with open(full_path, "rb") as f:
                        f.seek(start)
                        self.wfile.write(f.read(content_length))
            except (ValueError, IndexError):
                self.send_error(416, "Range Not Satisfiable")
                return
        else:
            self._send_cors_headers(200, full_path)
            self.send_header("Content-Type", self._guess_type(full_path))
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            if method == "GET":
                with open(full_path, "rb") as f:
                    self.wfile.write(f.read())

    def _send_cors_headers(self, status_code, path=None, content_range=None):
        self.send_response(status_code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Range, If-Range")
        self.send_header("Access-Control-Expose-Headers", "Content-Range, Accept-Ranges, Content-Length")
        self.send_header("Cache-Control", "no-store")
        if content_range is not None:
            self.send_header("Content-Range", content_range)

    def send_error(self, code, message=None, explain=None):
        try:
            short_msg, long_msg = self.responses.get(code, ("Error", "Unknown Error"))
            if message is None:
                message = short_msg
            if explain is None:
                explain = long_msg
            body = f"<html><body><h1>{code} {message}</h1><p>{explain}</p></body></html>".encode("utf-8", "replace")
            self._send_cors_headers(code, len(body))
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _resolve_path(self):
        requested_path = unquote(urlparse(self.path).path)
        root_path = self.server.root_path

        if os.path.isfile(root_path):
            base_dir = os.path.dirname(root_path)
            file_path = root_path
            if requested_path in ("", "/"):
                return file_path
            if os.path.basename(requested_path) == os.path.basename(file_path):
                return file_path
            return None

        base_dir = root_path
        candidate = os.path.normpath(os.path.join(base_dir, requested_path.lstrip("/")))
        try:
            if not os.path.commonpath([base_dir, candidate]) == base_dir:
                return None
        except ValueError:
            return None

        if os.path.isfile(candidate):
            return candidate
        return None

    def _guess_type(self, path):
        """Guess MIME type for file."""
        mime_type, _ = mimetypes.guess_type(path)
        if path.endswith(".pmtiles"):
            return "application/octet-stream"
        return mime_type or "application/octet-stream"

    def log_message(self, format, *args):
        """Log request details."""
        print(f"[{self.log_date_time_string()}] {format % args}")


def run_server(port=8000, root=None):
    """Run the PMTiles server."""
    if root is None:
        root = os.getcwd()

    root = os.path.abspath(root)

    server_address = ("0.0.0.0", port)
    httpd = PMTilesHTTPServer(server_address, RangeRequestHandler, root)

    print(f"PMTiles server started on http://0.0.0.0:{port}")
    print(f"Serving: {root}")
    print("Press Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    root = sys.argv[2] if len(sys.argv) > 2 else None

    run_server(port, root)
