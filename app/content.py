"""Load and validate site content at startup.

Pure content layer: no FastAPI imports. Reads ``content/data.yaml`` and every
``content/posts/*.md`` once, validates required fields, renders markdown, and returns
typed objects. Invalid content raises :class:`ContentError`, which fails the process at
boot rather than breaking a live page.
"""
from __future__ import annotations

import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

import frontmatter
import markdown
import yaml

from app.models import (
    Content,
    Education,
    Experience,
    Language,
    Post,
    Product,
    Profile,
    Role,
    SiteData,
    SkillGroup,
    SocialLink,
)

WORDS_PER_MINUTE = 200
REQUIRED_POST_FIELDS = ("title", "date", "tag", "excerpt")


class ContentError(Exception):
    """Raised when content files are missing required fields or malformed."""


# --------------------------------------------------------------------------- helpers


def _require(data: dict[str, Any], key: str, where: str) -> Any:
    if key not in data or data[key] in (None, ""):
        raise ContentError(f"{where}: missing required field '{key}'")
    return data[key]


def _as_date(value: Any, where: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError as exc:
            raise ContentError(f"{where}: date '{value}' is not YYYY-MM-DD") from exc
    raise ContentError(f"{where}: date must be a YYYY-MM-DD string, got {type(value).__name__}")


def _read_time(text: str) -> str:
    words = len(text.split())
    minutes = max(1, math.ceil(words / WORDS_PER_MINUTE))
    return f"{minutes} min read"


def _new_markdown() -> markdown.Markdown:
    return markdown.Markdown(
        extensions=["fenced_code", "tables", "toc", "codehilite"],
        extension_configs={"codehilite": {"guess_lang": False, "css_class": "codehilite"}},
    )


# ------------------------------------------------------------------------------ posts


def load_posts(posts_dir: Path) -> list[Post]:
    if not posts_dir.is_dir():
        return []

    md = _new_markdown()
    posts: list[Post] = []
    for path in sorted(posts_dir.glob("*.md")):
        where = f"post '{path.name}'"
        try:
            doc = frontmatter.load(path)
        except Exception as exc:  # malformed frontmatter
            raise ContentError(f"{where}: could not parse frontmatter ({exc})") from exc

        meta = doc.metadata
        for field_name in REQUIRED_POST_FIELDS:
            _require(meta, field_name, where)

        body = doc.content.strip()
        if not body:
            raise ContentError(f"{where}: body is empty")

        md.reset()
        posts.append(
            Post(
                slug=path.stem,
                title=str(meta["title"]),
                date=_as_date(meta["date"], where),
                tag=str(meta["tag"]),
                excerpt=str(meta["excerpt"]),
                body_html=md.convert(body),
                read=_read_time(body),
            )
        )

    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


# ------------------------------------------------------------------------------- data


def _social(item: dict[str, Any], i: int) -> SocialLink:
    where = f"data.yaml socials[{i}]"
    return SocialLink(
        label=str(_require(item, "label", where)),
        url=str(_require(item, "url", where)),
        icon=str(_require(item, "icon", where)),
    )


def _product(item: dict[str, Any], i: int) -> Product:
    where = f"data.yaml products[{i}]"
    return Product(
        initial=str(_require(item, "initial", where)),
        kind=str(_require(item, "kind", where)),
        name=str(_require(item, "name", where)),
        desc=str(_require(item, "desc", where)),
        stack=list(item.get("stack", [])),
    )


def _experience(item: dict[str, Any], i: int) -> Experience:
    where = f"data.yaml experience[{i}]"
    roles = [
        Role(title=str(_require(r, "title", f"{where}.roles")), span=str(r.get("span", "")))
        for r in item.get("roles", [])
    ]
    return Experience(
        company=str(_require(item, "company", where)),
        mono=str(_require(item, "mono", where)),
        type=str(item.get("type", "")),
        period=str(item.get("period", "")),
        tenure=str(item.get("tenure", "")),
        location=str(item.get("location", "")),
        roles=roles,
        impact=list(item.get("impact", [])),
        bullets=list(item.get("bullets", [])),
        stack=list(item.get("stack", [])),
    )


def _profile(data: dict[str, Any]) -> Profile:
    where = "data.yaml profile"
    p = _require(data, "profile", "data.yaml")
    return Profile(
        name=str(_require(p, "name", where)),
        greeting=str(p.get("greeting", "")),
        role=str(_require(p, "role", where)),
        location=str(p.get("location", "")),
        available_for_work=bool(p.get("available_for_work", False)),
        bio=str(_require(p, "bio", where)),
        initials=str(_require(p, "initials", where)),
    )


def load_data(data_path: Path) -> SiteData:
    if not data_path.is_file():
        raise ContentError(f"data file not found: {data_path}")
    try:
        raw = yaml.safe_load(data_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ContentError(f"data.yaml: invalid YAML ({exc})") from exc
    if not isinstance(raw, dict):
        raise ContentError("data.yaml: top level must be a mapping")

    return SiteData(
        profile=_profile(raw),
        socials=[_social(s, i) for i, s in enumerate(raw.get("socials", []))],
        products=[_product(p, i) for i, p in enumerate(raw.get("products", []))],
        experience=[_experience(e, i) for i, e in enumerate(raw.get("experience", []))],
        skills=[
            SkillGroup(
                cat=str(_require(g, "cat", f"data.yaml skills[{i}]")),
                items=list(g.get("items", [])),
            )
            for i, g in enumerate(raw.get("skills", []))
        ],
        education=[
            Education(
                degree=str(_require(e, "degree", f"data.yaml education[{i}]")),
                school=str(_require(e, "school", f"data.yaml education[{i}]")),
                span=str(e.get("span", "")),
                note=str(e.get("note", "")),
            )
            for i, e in enumerate(raw.get("education", []))
        ],
        languages=[
            Language(
                name=str(_require(lang, "name", f"data.yaml languages[{i}]")),
                level=str(lang.get("level", "")),
            )
            for i, lang in enumerate(raw.get("languages", []))
        ],
    )


# -------------------------------------------------------------------------------- all


def load_all(content_dir: Path) -> Content:
    """Load the full site content from ``content_dir`` (holds ``data.yaml`` and ``posts/``)."""
    site = load_data(content_dir / "data.yaml")
    posts = load_posts(content_dir / "posts")
    return Content(site=site, posts=posts)
