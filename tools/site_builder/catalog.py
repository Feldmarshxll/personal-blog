"""Derive URLs, taxonomy pages and ordered publication series."""

import hashlib
import re


MONTHS = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
          'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря')


def date_label(value):
    return f'{value.day} {MONTHS[value.month - 1]} {value.year}'


def tag_id(title):
    normalized = title.strip().casefold()
    readable = re.sub(r'[^a-z0-9]+', '-', normalized).strip('-')[:32] or 'tag'
    return readable + '-' + hashlib.sha256(normalized.encode()).hexdigest()[:8]


def link(entry):
    return {'title': entry['title'], 'url': entry['url']}


def decorate(articles, projects, categories, series, base):
    """Enrich the loaded catalog only after publication filtering."""
    category_map = {c['id']: dict(c, url=f'{base}blog/categories/{c["id"]}/') for c in categories}
    series_map = {s['id']: dict(s, url=f'{base}blog/series/{s["id"]}/', articles=[]) for s in series}
    tags = {}
    for article in articles:
        article['url'] = f'{base}blog/articles/{article["slug"]}/'
        article['date_label'] = date_label(article['date'])
        article['category_info'] = category_map[article['category']]
        article['tag_info'] = []
        for title in article['tags']:
            key = tag_id(title)
            tag = tags.setdefault(key, dict(id=key, title=title, url=f'{base}blog/tags/{key}/', articles=[]))
            if article not in tag['articles']:
                tag['articles'].append(article)
                article['tag_info'].append(link(tag))
        if article.get('series'):
            series_map[article['series']]['articles'].append(article)
    for group in series_map.values():
        group['articles'].sort(key=lambda article: article['series_order'])
        for index, article in enumerate(group['articles']):
            article['series_info'] = dict(
                link(group),
                previous=link(group['articles'][index - 1]) if index else None,
                next=link(group['articles'][index + 1]) if index + 1 < len(group['articles']) else None,
            )
    for project in projects:
        project.update(url=f'{base}blog/projects/{project["slug"]}/', description=project['summary'])
    return list(category_map.values()), list(series_map.values()), sorted(tags.values(), key=lambda tag: tag['title'].casefold())


def summary(entry):
    return {key: entry[key] for key in ('title', 'description', 'url', 'date_label') if key in entry}
