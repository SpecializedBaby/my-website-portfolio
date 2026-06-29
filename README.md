# Portfolio Website

Personal portfolio for Dmytro Kostevskyi — a writing feed, projects, and resume —
built with FastAPI + Jinja2 and deployed on FastAPI Cloud.

Posts are markdown files; everything else lives in one editable YAML file. No database,
no auth. Content is parsed into memory once at startup.

## Layout

```
app/                FastAPI app, content loader, templates, static assets
content/data.yaml   profile, socials, products, experience, skills, education, languages
content/posts/*.md  one markdown file per post (frontmatter: title, date, tag, excerpt)
tests/              pytest suite
```

## Develop

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
fastapi dev app/main.py        # http://127.0.0.1:8000
pytest
```

## Publish a post

Add `content/posts/<slug>.md` with frontmatter, then redeploy:

```markdown
---
title: My Post Title
date: 2026-06-01
tag: Architecture
excerpt: One-sentence summary shown in the feed.
---

Body in **markdown**. Code blocks are syntax-highlighted.
```

## Edit other content

Edit `content/data.yaml` (profile, projects, experience, skills, education, languages)
and redeploy.

## Deploy (FastAPI Cloud)

```bash
fastapi login
fastapi deploy
```

Re-run `fastapi deploy` to publish changes. CI (deploy on push) can be added later with
`fastapi cloud setup-ci`; a custom domain is attached in the dashboard under Domains.
