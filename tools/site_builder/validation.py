"""Small source-aware validators shared by content loaders."""

from datetime import date, datetime
import math
from pathlib import Path
import re
from urllib.parse import urlsplit

import yaml


class ContentError(ValueError):
    """An authored file cannot be published safely or unambiguously."""


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate YAML mapping keys instead of silently losing data."""


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ContentError(f'Ключ YAML должен быть строкой, строка {key_node.start_mark.line + 1}')
        if key in result:
            raise ContentError(f'Повторный ключ YAML: {key}, строка {key_node.start_mark.line + 1}')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def fail(source, message):
    raise ContentError(f'{source}: {message}')


def parse_yaml(text, source):
    try:
        value = yaml.load(text, Loader=UniqueLoader)
    except (yaml.YAMLError, ContentError) as exc:
        fail(source, str(exc))
    if not isinstance(value, dict):
        fail(source, 'ожидается YAML-объект')
    return value


def read_yaml(path):
    try:
        return parse_yaml(path.read_text(encoding='utf-8-sig'), path)
    except OSError as exc:
        fail(path, str(exc))


def text(value, source, field, *, empty=False):
    if not isinstance(value, str) or (not empty and not value.strip()):
        fail(source, f'{field}: требуется строка' + ('' if empty else ' с текстом'))
    return value


def identifier(value, source, field='id'):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        fail(source, f'{field}: требуется идентификатор из a-z, 0-9 и дефисов')
    return value


def route_identifier(value, source, field='id'):
    value = identifier(value, source, field)
    if value == 'index':
        fail(source, f'{field}: index зарезервирован для страницы раздела')
    return value


def records(value, source, field):
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        fail(source, f'{field}: требуется список объектов')
    return value


def unique_records(value, source, field):
    result, seen = records(value, source, field), set()
    for item in result:
        key = identifier(item.get('id'), source, f'{field}.id')
        if key in seen:
            fail(source, f'{field}: повторный id {key}')
        seen.add(key)
    return result


def string_list(value, source, field):
    if not isinstance(value, list):
        fail(source, f'{field}: требуется список строк')
    for item in value:
        text(item, source, field)
    return list(dict.fromkeys(value))


def boolean(value, source, field):
    if type(value) is not bool:
        fail(source, f'{field}: требуется true или false')
    return value


def positive_number(value, source, field, *, zero=False):
    if (type(value) not in (int, float) or not math.isfinite(value)
            or value < 0 or (not zero and value == 0)):
        fail(source, f'{field}: требуется конечное ' + ('неотрицательное' if zero else 'положительное') + ' число')
    return value


def calendar_date(value, source, field):
    if isinstance(value, datetime):
        fail(source, f'{field}: используйте дату YYYY-MM-DD без времени')
    if isinstance(value, date):
        return value
    try:
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError()
        return date.fromisoformat(value)
    except ValueError:
        fail(source, f'{field}: требуется существующая дата YYYY-MM-DD')


def web_url(value, source, field):
    text(value, source, field)
    try:
        parsed = urlsplit(value)
        if (parsed.scheme not in ('https', 'http') or not parsed.hostname
                or parsed.username or parsed.password or any(ord(c) < 32 for c in value)):
            raise ValueError()
    except ValueError:
        fail(source, f'{field}: требуется полный http(s) URL')
    return value


def links(value, source, field):
    for link in records(value, source, field):
        text(link.get('label'), source, f'{field}.label')
        web_url(link.get('url'), source, f'{field}.url')
    return value


def inside(path, parent):
    """Resolve symlinks before checking boundaries, including Windows junctions."""
    resolved, boundary = Path(path).resolve(), Path(parent).resolve()
    if resolved == boundary or not resolved.is_relative_to(boundary):
        fail(path, f'путь должен находиться внутри {boundary}')
    return resolved
