"""Validate links and fragments in the built site without network access."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class References(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links = set(), []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('id'):
            self.ids.add(values['id'])
        for attr in ('href', 'src', 'poster'):
            if values.get(attr):
                self.links.append(values[attr])


def check_links(site_dir, base_path, origin):
    root = Path(site_dir).resolve()
    if not (root / 'index.html').exists():
        return ['Сначала соберите сайт: не найден index.html']
    documents = {}
    for path in sorted(root.rglob('*.html')):
        parser = References()
        parser.feed(path.read_text(encoding='utf-8'))
        documents[path] = parser
    problems = []
    origin_host = urlsplit(origin).netloc
    for source, document in documents.items():
        for reference in document.links:
            url = urlsplit(reference)
            if url.scheme in ('data', 'mailto', 'tel'):
                continue
            if url.netloc and url.netloc != origin_host:
                continue
            if url.scheme and url.scheme not in ('https', 'http'):
                problems.append(f'{source.relative_to(root)}: недопустимая ссылка {reference}')
                continue
            path = unquote(url.path)
            if path.startswith('/'):
                if not path.startswith(base_path):
                    problems.append(f'{source.relative_to(root)}: ссылка вне базового пути: {reference}')
                    continue
                target = root / path[len(base_path):]
            else:
                target = source.parent / path if path else source
            target = target.resolve()
            if not target.is_relative_to(root):
                problems.append(f'{source.relative_to(root)}: выход за каталог сайта: {reference}')
                continue
            if target.is_dir():
                target /= 'index.html'
            if not target.is_file():
                problems.append(f'{source.relative_to(root)}: не найден {reference}')
            elif url.fragment and target in documents and unquote(url.fragment) not in documents[target].ids:
                problems.append(f'{source.relative_to(root)}: не найден якорь {reference}')
    return problems
