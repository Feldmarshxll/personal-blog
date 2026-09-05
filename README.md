# Feldmarshxll & SuperciliosMe

Личный сайт: статьи, серии публикаций, проекты, резюме и вишлисты. Статический HTML собирается Zensical; небольшой Python-генератор готовит страницы из Markdown и YAML.

## Запуск

Нужен Python 3.14. В корне проекта, PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements/lock.txt
.\.venv\Scripts\python.exe -m tools.site_builder serve
```

Linux/macOS:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements/lock.txt
.venv/bin/python -m tools.site_builder serve
```

Адрес предпросмотра: <http://127.0.0.1:8000/personal-blog/>. После изменения `content/`, `theme/` или `zensical.toml` сайт пересобирается; обновите страницу браузера. После правок Python-кода перезапустите `serve`. Для другого порта добавьте `--port 8001`. Для локального просмотра черновиков и будущих статей используйте `serve --drafts`. Остановка — Ctrl+C.

## Структура

| Каталог | Назначение |
| --- | --- |
| `content/` | Редактируемые статьи, проекты, страницы, вишлисты и настройки содержимого |
| `theme/overrides/` | Собственные HTML-шаблоны Zensical |
| `theme/assets/` | Стили, JavaScript и изображения интерфейса |
| `tools/site_builder/` | Валидация, каталоги публикаций, генератор, предпросмотр и проверка ссылок |
| `tests/` | Проверки генерации и правил публикации |
| `examples/` | Образцы статьи и проекта; не публикуются |
| `docs/` | Инструкции по поддержке сайта; не публикуются |
| `plans/` | Согласованное проектирование и план реализации; не публикуются |
| `requirements/` | Зафиксированные зависимости |
| `.build/` | Генерируемые страницы, HTML и локальные отчёты; игнорируется Git |

`zensical.toml` задаёт адрес, параметры сборки и дерево страниц Zensical. Видимое меню собственной темы находится в `theme/overrides/main.html`; при изменении разделов обновляйте оба файла. В `.gitignore` исключены виртуальное окружение, кэши, локальные настройки и результаты сборки. Сгенерированные файлы не редактируются вручную.

## Проверки

В PowerShell:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m tools.site_builder build
.\.venv\Scripts\python.exe -m tools.site_builder check
```

Для Linux/macOS замените путь к интерпретатору на `.venv/bin/python`.

`build` сначала проверяет содержимое, затем выполняет чистую строгую сборку Zensical. `check` проверяет файлы и якоря внутренних ссылок в готовом HTML. Внешние магазины и сайты он не опрашивает. `generate` выполняет только подготовку Markdown.

## Публикация

GitHub Actions проверяет pull request, основную ветку и ветки `codex/**`. После успешных проверок push в `main` или `master` публикует `.build/site` в существующую ветку `gh-pages`. Источник Pages в настройках репозитория должен оставаться **Deploy from a branch → gh-pages → /(root)**. Ручной запуск workflow выполняет только проверки.

Статьи с `draft: true` и датой в будущем исключаются из публичной сборки. Чтобы опубликовать материал с наступившей датой, нужна новая сборка, например после push. RSS в этой версии отсутствует.

Подробнее: [ведение содержимого](docs/authoring.md), [устройство и обслуживание](docs/development.md).
