# Personal Site Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans. Independent content and visual tasks may run in parallel with explicit file ownership.

**Goal:** Build the approved personal site on Zensical, with YAML wishlists, structured publishing and a cosmic homepage.

**Architecture:** Python validates YAML and Markdown and stages publishable files in `.build/docs`. Zensical renders them using project-owned templates and assets into `.build/site`. Handwritten inputs never share directories with generated output.

**Tech Stack:** Python 3.14, Zensical, PyYAML, Python unittest, HTML/CSS/JavaScript.

**Spec:** `plans/2026-09-05-personal-site-design.md`, approved by the user.

## Global constraints

- Work only on `codex/personal-site-zensical`, based on current `main` at ec44996.
- Brand: `Feldmarshxll & SuperciliosMe`. Russian copy, no decorative emoji.
- Dark cosmic design with animated black hole and readable minimalist internal pages.
- Navigation: Главная; Блог и портфолио (Статьи, Серии, Проекты, Резюме); Личное.
- Categories: Разработка, Data Science, Исследования. No RSS.
- Preserve existing wishlist entries, source currencies, links, comments and goals. Do not invent author biographies or articles.
- Static deployment base path `/personal-blog/`; support old wishlist URLs.
- Generated output, virtual environments, caches, reports and local previews are ignored by Git.
- Do not merge, push or publish as part of this local implementation.

## File boundaries and interfaces

- `content/site.yml`: site name, tagline, intro, categories (list of `{id, title}`). The custom theme owns the displayed navigation; TOML mirrors the page structure for Zensical.
- `content/wishlists/*.yml`: list `{id, title, description, legacy_path, categories: [{id, title}], items: [{id, title, description, category, kind, links: [{label, url}], price?, currency?, status, priority?, image?, checked_at?}], footer_links: [{label, url}]}`. kind is `product` or `goal`; price is a number, currency RUB or USD. Status `wanted` or `received`. Metadata without evidence stays absent.
- `content/articles/*.md`, `content/projects/*.md`, `content/pages/resume.md`: editable Markdown; article front matter includes title/date/description/category/tags/slug/draft and optional series/series_order/authors. Project metadata includes title/summary/status/technologies/slug/featured.
- `content/series.yml`: series records `{id, title, description}`.
- `examples/`: unpublished starter Markdown; `docs/`: maintenance and authoring guides, outside public inputs.
- `tools/site_builder/`: validation, content catalog, generation and CLI, split by responsibility. Public entry point `python -m tools.site_builder {generate,build,serve,check}`.
- `theme/overrides/main.html`: complete Zensical page template, uses `page.content`, `page.title`, `page.meta`, `config.site_name`, `config.extra.base_path`; assets and navigation resolved using base_path (trailing slash).
- `theme/overrides/home.html`: homepage template, uses `page.meta.site` and `page.meta.latest_articles` / `featured_projects` (lists of title, description, url, date_label optional).
- `theme/overrides/article.html`: article template, uses `page.meta.article` containing date_label, category `{title,url}`, tags `[{title,url}]`, authors, series `{title,url,previous?,next?}`; link objects use title,url.
- `theme/assets/styles/site.css`, `theme/assets/scripts/site.js`, `theme/assets/scripts/black-hole.js`: appearance and enhancement only. Generator stages assets as `assets/`.
- All generated links in metadata include the configured base_path. `main.html` exposes template blocks `head_extra`, `content`, `scripts_extra`.
- Generator HTML contract: `.eyebrow`, `.page-intro`, `.section-heading`, `.card-grid`, `.content-card`, `.card-meta`, `.tag`, `.empty-state`, `.wishlist`, `.wishlist-toolbar`, `.wish-card`, `.wish-category`, `.wish-price`, `.wish-description`, `.wish-links`, `.wishlist-count`, `.series-list`. The frontend agent can extend these with written notice.
- Wishlist enhancement contract: root `[data-wishlist]`, cards `[data-wish]` with data-category/status/currency/price (empty for goals), controls `[data-filter-category]`, `[data-filter-status]`, `[data-filter-currency]`, `[data-filter-budget]`, reset `[data-filter-reset]`, count `[data-filter-count]`, empty `[data-filter-empty]`. Budget only filters chosen currency; unknown prices remain visible, cross-currency products hidden while a currency-specific budget is active. JS sets hidden on cards and announces count.
- `tests/`: real filesystem-based generator tests and rendered output checks.
- `requirements/`: pinned runtime dependency input and resolved lock; root `.python-version`, `zensical.toml`, `README.md` and small tooling config only.

## Task 1: Repository, environment and Zensical baseline

- [x] Inspect branch, current files and authorized scope; create feature branch.
- [x] Add `.gitignore`, `.editorconfig`, `.gitattributes`.
- [x] Create ignored `.venv`, install Zensical and PyYAML, record versions.
- [x] Build original content into ignored baseline output to establish compatibility.

Run: `.venv/Scripts/python -m pip install zensical pyyaml`; then the installed `zensical build` against an isolated baseline config.

## Task 2: Content migration (independent file owner)

- [x] Create the YAML and Markdown inputs defined above; preserve all current source wishlist records.
- [x] Add empty but intentional resume sections and unpublished article/project examples.
- [x] Verify source item counts, descriptions and exact link sets against migrated YAML.
- [x] Review schema compliance and content preservation before removing the old published Markdown.

## Task 3: Generator and content catalogs

Public interfaces: `load_site(root: Path) -> dict`, `load_wishlists(root: Path) -> list[dict]`, `load_articles(root: Path, today: date, preview: bool = False) -> list[dict]`, `generate(root: Path, preview: bool = False, today: date | None = None) -> Path`. Errors subclass `ValueError` and include source location. Root is an explicitly supplied repository or temporary fixture.

- [x] Write failing unittest cases for duplicate ids, multiple links, missing price goals, invalid YAML, unsafe URLs and outside-root output protection.
- [x] Run `python -m unittest discover -s tests -v` and verify failures identify missing validation/generation.
- [x] Implement loaders with safe YAML parsing, required fields, type validation and canonical ASCII identifiers.
- [x] Write failing catalog tests for drafts, future dates, duplicate slugs, duplicate series order and previous/next ordering.
- [x] Implement article and project catalogs, deterministic indexes and templates' metadata contract.
- [x] Generate staged Markdown and assets. Before replacing output, resolve and verify `.build/docs` is inside repository `.build`. Never recursively delete caller-supplied paths.
- [x] Add integration tests: removed pages disappear on rebuild; source content stays unchanged; old wishlist URLs link to new pages; only published files enter staging.

Example behavioral assertion:

```python
generate(root, today=date(2026, 9, 5))
self.assertFalse((root / '.build/docs/blog/articles/future.md').exists())
self.assertTrue((root / '.build/docs/personal/wishlists/mine.md').exists())
```

## Task 4: Theme and animation (independent file owner)

- [x] Build own page shell, home and article templates using the defined context.
- [x] Implement responsive dark layout, restrained warm accent, navigation and graceful empty states.
- [x] Implement decorative black hole with static fallback, reduced motion, pause control, visibility and viewport lifecycle handling.
- [x] Implement progressive wishlist filters using the agreed data attributes; keep source content accessible without JS.
- [x] Root integrates generated markup and performs browser checks at wide and narrow viewport widths. Visual fixes remain in theme files.

## Task 5: CLI, CI and authoring workflow

- [x] Implement `build` as generation plus subprocess Zensical; exit nonzero on validation/build errors.
- [x] Implement `serve` with rebuild-on-source-change, a loopback HTTP server, correct `/personal-blog/` prefix and readable errors without replacing a successful build on invalid input.
- [x] Implement `check` to validate built local href/src links and anchors, excluding outbound URLs.
- [x] Add GitHub Actions tests and strict build for pull requests; publish only main/master after checks.
- [x] Write README and authoring guide with exact commands for PowerShell and POSIX, schema, draft policy and content location.

## Task 6: Verification and delivery

- [x] Run full tests, strict build and local link check.
- [x] Verify homepage, articles/series using isolated preview fixtures, projects, resume and both wishlists in a browser, including reduced motion and filtering.
- [x] Review all changed code for correctness and spec compliance, resolve findings.
- [x] Check Git status/ignored output, final branch name and whitespace.
- [x] Keep feature branch separate. Provide full source modules as a generated ignored downloadable text bundle in addition to normal source links, to satisfy the user's full-code delivery preference without duplicating source inside tracked files.

## Execution record

- Branch created at ec44996; current main already includes merged wishlist updates.
- Separate branch in the existing checkout follows the user's request; an additional worktree is unnecessary.
- Separate generators and static data keep unsupported blog plugins out of the runtime.

- Final verification: 33 tests passed, including a real Zensical build of isolated articles, series and projects; strict public build and internal link checks passed.
- Browser checks covered desktop/mobile layouts, keyboard navigation, filters, both legacy redirects, 404 and static pages without JavaScript. The actual animation script passed an isolated lifecycle check with emulated browser services.
- The runtime configuration is generated as ignored .build/zensical.yml. Relative paths avoid an absolute-path incompatibility observed in the Windows Zensical build.
- Independent review findings were fixed and narrowly rechecked. Local reports and the complete source bundle stay under ignored .build/reports/.
