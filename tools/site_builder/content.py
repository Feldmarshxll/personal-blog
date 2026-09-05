"""Metadata catalogs: canonical addresses and explicit publication policy."""

from datetime import date
from pathlib import Path

from .validation import (ContentError, boolean, calendar_date, fail,
                         links, parse_yaml, read_yaml,
                         route_identifier, string_list, text, unique_records)
from .wishlists import load_wishlists


def load_site(root):
    source = root / 'content/site.yml'
    data = read_yaml(source)
    text(data.get('name'), source, 'name')
    for field in ('tagline', 'intro'):
        data.setdefault(field, '')
        text(data[field], source, field, empty=True)
    for category in unique_records(data.get('categories', []), source, 'categories'):
        route_identifier(category['id'], source, 'categories.id')
        text(category.get('title'), source, 'categories.title')
    return data


def load_series(root):
    source = root / 'content/series.yml'
    if not source.exists():
        return []
    series = unique_records(read_yaml(source).get('series', []), source, 'series')
    for entry in series:
        route_identifier(entry['id'], source, 'series.id')
        text(entry.get('title'), source, 'series.title')
        entry.setdefault('description', '')
        text(entry['description'], source, 'series.description', empty=True)
    return series


def read_markdown(path):
    raw = path.read_text(encoding='utf-8-sig').replace('\r\n', '\n')
    if not raw.startswith('---\n'):
        fail(path, 'нужен блок метаданных между строками ---')
    sections = raw.split('\n---\n', 1)
    if len(sections) != 2:
        fail(path, 'не закрыт блок метаданных ---')
    metadata = parse_yaml(sections[0][4:], path)
    return metadata, sections[1].lstrip('\n')


def _catalog(root, kind, today, preview):
    entries, slugs, positions = [], set(), set()
    categories = {item['id'] for item in load_site(root).get('categories', [])}
    series = {item['id'] for item in load_series(root)}
    for path in sorted((root / f'content/{kind}').rglob('*.md')):
        data, body = read_markdown(path)
        slug = route_identifier(data.get('slug'), path, 'slug')
        if slug in slugs:
            fail(path, f'повторный slug {slug}')
        slugs.add(slug)
        text(data.get('title'), path, 'title')
        draft = boolean(data.get('draft', False), path, 'draft')
        data['authors'] = string_list(data.get('authors', []), path, 'authors')
        if kind == 'articles':
            data['date'] = calendar_date(data.get('date'), path, 'date')
            text(data.get('description'), path, 'description')
            if data.get('category') not in categories:
                fail(path, 'неизвестная category (см. content/site.yml)')
            data['tags'] = string_list(data.get('tags', []), path, 'tags')
            if 'series' in data:
                if data['series'] not in series:
                    fail(path, 'неизвестная series (см. content/series.yml)')
                order = data.get('series_order')
                if type(order) is not int or order <= 0:
                    fail(path, 'series_order должен быть положительным целым числом')
                position = (data['series'], order)
                if position in positions:
                    fail(path, f'повторный series_order {position}')
                positions.add(position)
            elif 'series_order' in data:
                fail(path, 'series_order требует series')
            if not preview and (draft or data['date'] > today):
                continue
        else:
            text(data.get('summary'), path, 'summary')
            text(data.get('status'), path, 'status')
            data['featured'] = boolean(data.get('featured', False), path, 'featured')
            data['technologies'] = string_list(data.get('technologies', []), path, 'technologies')
            links(data.get('links', []), path, 'links')
            data.setdefault('links', [])
            if not preview and draft:
                continue
        data.update(body=body, source=path, draft=draft)
        entries.append(data)
    if kind == 'articles':
        entries.sort(key=lambda entry: (-entry['date'].toordinal(), entry['slug']))
    else:
        entries.sort(key=lambda entry: (not entry['featured'], entry['title'].casefold()))
    return entries


def load_articles(root, today, preview=False):
    return _catalog(Path(root), 'articles', today, preview)


def load_projects(root, preview=False):
    return _catalog(Path(root), 'projects', date.today(), preview)
