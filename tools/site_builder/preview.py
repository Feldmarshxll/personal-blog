"""Loopback preview with base-path routing and source-change rebuilds."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import threading
from urllib.parse import urlsplit


def signature(root):
    sources = [root / name for name in ('content', 'theme')]
    files = [p for source in sources for p in source.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts]
    files.extend([root / 'zensical.toml'])
    return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in sorted(files))


def serve(root, site_dir, base_path, port, rebuild):
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/' or path == base_path.rstrip('/'):
                self.send_response(302)
                self.send_header('Location', base_path)
                self.end_headers()
                return
            if not path.startswith(base_path):
                self.send_error(404)
                return
            self.path = '/' + self.path[len(base_path):]
            super().do_GET()

        def end_headers(self):
            self.send_header('Cache-Control', 'no-store')
            super().end_headers()

    server = ThreadingHTTPServer(('127.0.0.1', port), partial(Handler, directory=str(site_dir)))
    stopping = threading.Event()

    def watch():
        previous = signature(root)
        while not stopping.wait(0.7):
            try:
                current = signature(root)
                if current != previous:
                    previous = current
                    print('Изменены исходники. Пересборка…', flush=True)
                    rebuild()
                    print('Готово. Обновите страницу браузера.', flush=True)
            except Exception as exc:
                print(f'Предпросмотр: {exc}', flush=True)

    worker = threading.Thread(target=watch, daemon=True)
    worker.start()
    print(f'Предпросмотр: http://127.0.0.1:{server.server_port}{base_path}', flush=True)
    print('Ctrl+C — остановить. После изменения содержимого обновите страницу.', flush=True)
    try:
        server.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        pass
    finally:
        stopping.set()
        server.server_close()
        worker.join(timeout=2)
