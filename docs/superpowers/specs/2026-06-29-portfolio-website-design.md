# Portfolio Website — Design Spec

**Date:** 2026-06-29
**Author:** Dmytro Kostevskyi
**Status:** Approved for planning

## Summary

A personal portfolio website for Dmytro Kostevskyi (Solution Architect, Tenerife, Spain)
with three sections — **Posts** (a writing feed), **Products** (projects), and **Resume**
(experience, skills, education, languages). The visual design already exists as a Claude
Design project and is reproduced exactly; this spec covers turning it into a deployable
FastAPI application served on FastAPI Cloud (free tier: 0.1 vCPU / 512 MB, 1 custom domain).

Posts are authored as markdown files committed to the repo. All other content lives in a
single editable YAML file. There is no database and no authentication.

## Goals

- Reproduce the existing design pixel-for-pixel (light/dark theme, tabbed layout).
- Let Dmytro publish posts by adding a markdown file and redeploying.
- Keep content (projects, experience, skills, profile) editable in one YAML file, separate
  from code.
- Each post has its own shareable, SEO-indexable URL.
- Run comfortably within 0.1 vCPU / 512 MB on FastAPI Cloud with one custom domain.

## Non-Goals (YAGNI)

- No database, no admin panel, no login/auth.
- No contact form (the design uses `mailto:` and social links).
- No comments, analytics, or newsletter.
- No CMS — publishing is "add a markdown file, commit, redeploy".

## Approach

**FastAPI + Jinja2, content loaded into memory at startup.** FastAPI server-renders the
portfolio page (all three tabs present in the HTML) and a full article page per post.
Markdown posts and a YAML data file are parsed once at startup and cached in memory, so
requests are instant and the footprint is tiny. Tab switching and the theme toggle are
vanilla JS ported from the design. The Claude Design `DCLogic` runtime is removed.

Two alternatives were rejected: a static-site generator (barely uses FastAPI, adds a build
step) and per-request markdown rendering (wastes CPU for no benefit at this scale).

## Architecture

### Project layout

```
my-portfolio/
  app/
    __init__.py
    main.py            # FastAPI app, route handlers, startup content load
    content.py         # load + validate posts (markdown) and data.yaml
    models.py          # dataclasses: Profile, SocialLink, Product, Experience, Post, etc.
    templates/
      base.html        # <head>, fonts, theme CSS link, shared chrome
      index.html       # the tabbed portfolio page (Posts / Products / Resume)
      post.html        # single article page
      404.html         # styled not-found
    static/
      styles.css       # theme variables + base rules lifted from the design
      resume.pdf       # downloadable resume
      favicon.svg
  content/
    data.yaml          # profile, socials, products, experience, skills, education, languages
    posts/
      2026-05-whatsapp-migration.md
      ... (6 seed posts from the design)
  tests/
    test_routes.py
    test_content.py
  requirements.txt
  pyproject.toml
  README.md
```

### Components and responsibilities

- **`content.py`** — pure content layer. Reads `content/data.yaml` and every
  `content/posts/*.md`, parses frontmatter, computes read-time, sorts posts newest-first,
  validates required fields, and returns typed objects. No FastAPI imports. Independently
  unit-testable.
- **`models.py`** — plain dataclasses describing the content shapes. The single source of
  truth for what fields templates can rely on.
- **`main.py`** — FastAPI app. On startup, calls `content.load_all()` once and stores the
  result in app state. Defines routes, renders Jinja templates, mounts static files.
- **Templates** — own markup and presentation only. They consume the typed content; they
  do not read files or compute anything beyond simple display formatting.

This keeps a clean boundary: content loading is testable without HTTP, and routing is
testable without touching the filesystem details.

### Routes

| Method | Path             | Response |
|--------|------------------|----------|
| GET    | `/`              | Full portfolio page. All three tabs server-rendered into the HTML. Default visible tab: **Posts**. |
| GET    | `/posts/{slug}`  | Full article page for that post; 404 if unknown. |
| GET    | `/resume.pdf`    | The resume PDF (served from `static/`). |
| GET    | `/healthz`       | `200 {"status":"ok"}` for platform health checks. |
| (mount)| `/static/*`      | Static assets. |

Unknown routes and unknown post slugs render the styled `404.html` with status 404.

### Client-side behavior (vanilla JS, ported from the design)

- **Tabs:** clicking Posts / Products / Resume toggles which section is visible. All
  sections exist in the DOM for SEO; JS only changes visibility and active-tab styling.
- **Deep-linking:** the URL hash selects a tab (`/#posts`, `/#products`, `/#resume`). On
  load, the hash (if present) determines the active tab; otherwise the default (Posts) is
  shown. Article pages link back to `/#posts`.
- **Theme toggle:** light/dark, **persisted in `localStorage`**. On first visit with no
  stored preference, respect `prefers-color-scheme`. (Improvement over the design, which
  did not persist.)

## Content Model

### Posts (`content/posts/*.md`)

- **Slug** = filename without extension (e.g. `2026-05-whatsapp-migration`).
- **Frontmatter (YAML):**
  - `title` (required, string)
  - `date` (required, `YYYY-MM-DD`)
  - `tag` (required, string — e.g. "Architecture")
  - `excerpt` (required, string — shown in the feed list)
- **Body:** markdown; rendered to HTML with fenced code blocks, tables, and headings.
- **Read-time:** auto-computed from body word count (~200 wpm), displayed as "N min read".
- **Ordering:** newest `date` first.

The 6 posts already written in the design are seeded as starter `.md` files (full bodies
written from their excerpts/topics so each article page has real content).

### Structured content (`content/data.yaml`)

Holds everything else, seeded from the design's current values:

- `profile`: name, greeting, role, location, available_for_work (bool), bio (with the
  emphasized phrases), avatar initials.
- `socials`: list of `{label, url, icon}` (LinkedIn, GitHub, Telegram, Email).
- `products`: list of `{initial, kind, name, desc, stack[]}`.
- `experience`: list of `{company, mono, type, period, tenure, location, roles[], impact[],
  bullets[], stack[]}`.
- `skills`: list of `{cat, items[]}`.
- `education`: list of `{degree, school, span, note}`.
- `languages`: list of `{name, level}`.

Editing the site's content = editing `data.yaml` and committing; no code changes.

## Markdown Rendering

- Library: `markdown` (Python) with extensions: `fenced_code`, `tables`, `toc`.
- Code blocks: server-side syntax highlighting via the `codehilite` extension (Pygments),
  themed for light/dark with CSS variables. (Posts are technical; nice code blocks matter.)
- Rendered HTML is produced at startup and cached on the Post object.

## Visual Fidelity

- The design's exact markup and inline styles are preserved inside the Jinja templates,
  with dynamic regions driven by `for`-loops over the typed content.
- Only the `:root` / `[data-theme="dark"]` CSS-variable block and base resets are lifted
  into `static/styles.css`.
- Google Fonts (Space Grotesk, DM Sans, JetBrains Mono) loaded as in the design.
- Result: identical appearance; the `DCLogic` runtime and `<x-dc>` wrappers are gone.

## Error Handling

- **Startup validation:** `content.load_all()` validates every post's frontmatter and the
  `data.yaml` schema. Missing/invalid required fields raise a clear exception that fails
  the process at boot — a broken content file never reaches a live page.
- **Unknown post slug:** 404 with the styled `404.html`.
- **Empty posts list:** the Posts tab shows a tasteful empty state instead of a blank area.
- **Missing `resume.pdf`:** the Download button is omitted if the file is absent (checked
  at startup).

## Testing

`pytest` + FastAPI `TestClient`.

- **`test_routes.py`**
  - `/` returns 200 and contains the profile name and a known seed-post title.
  - A valid `/posts/{slug}` returns 200 and contains that post's title and rendered body.
  - An unknown `/posts/{slug}` returns 404.
  - `/healthz` returns 200.
- **`test_content.py`**
  - Frontmatter parsing produces the expected fields; slug derives from filename.
  - Posts sort newest-first.
  - Read-time computes correctly for a known word count.
  - Missing required frontmatter field raises a validation error.
  - `data.yaml` loads into the expected dataclasses.

## Deployment (FastAPI Cloud)

- Single uvicorn worker; content cached in memory; no DB → fits 0.1 vCPU / 512 MB.
- App object exposed as `app` in `app/main.py`.
- Dependencies pinned in `requirements.txt` (fastapi, uvicorn, jinja2, markdown, pygments,
  pyyaml, python-frontmatter).
- The app binds to the platform-provided port/host.
- **Open items to confirm at implementation time** (not blockers for planning):
  - Exact FastAPI Cloud deploy command and any required config file (e.g. a project/TOML
    file) and the app-path convention.
  - Custom domain attachment step — requires Dmytro's domain name.

## Open Decisions Resolved

- Post management: **markdown files in the repo**.
- Post pages: **full article page per post**.
- Resume: **PDF download** + **editable YAML data file** for projects/experience/skills.
- Default landing tab: **Posts** (better first impression for a feed-oriented portfolio).
