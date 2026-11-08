"""Serve the CROSSFADE site locally with caching switched off (used by boot_site.ps1).

python's plain http.server lets the browser keep pages it has seen: a panel opened yesterday can be shown from the
browser's cache today, so a page updated since (a new button, a new status) looks unchanged until a hard refresh.
This server sends Cache-Control: no-store with every file, so every load reads the file on disk.

    python tools/serve.py 8000
"""
import http.server, sys


class NoCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"      serving http://127.0.0.1:{port}/ (no caching)", flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", port), NoCache).serve_forever()


if __name__ == "__main__":
    main()
