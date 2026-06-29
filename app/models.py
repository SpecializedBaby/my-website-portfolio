"""Typed content shapes for the portfolio site.

These dataclasses are the single source of truth for the fields templates may rely on.
They mirror the field names used in the original Claude Design mockup so the templates
map 1:1 onto the content.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class SocialLink:
    label: str
    url: str
    icon: str  # key into the SVG icon set in the template


@dataclass(frozen=True)
class Profile:
    name: str
    greeting: str
    role: str
    location: str
    available_for_work: bool
    bio: str  # may contain <span> emphasis markup; rendered as-is (trusted, author-owned)
    initials: str


@dataclass(frozen=True)
class Product:
    initial: str
    kind: str
    name: str
    desc: str
    stack: list[str]


@dataclass(frozen=True)
class Role:
    title: str
    span: str


@dataclass(frozen=True)
class Experience:
    company: str
    mono: str
    type: str
    period: str
    tenure: str
    location: str
    roles: list[Role]
    impact: list[str]
    bullets: list[str]
    stack: list[str]


@dataclass(frozen=True)
class SkillGroup:
    cat: str
    items: list[str]


@dataclass(frozen=True)
class Education:
    degree: str
    school: str
    span: str
    note: str = ""


@dataclass(frozen=True)
class Language:
    name: str
    level: str


@dataclass(frozen=True)
class Post:
    slug: str
    title: str
    date: date
    tag: str
    excerpt: str
    body_html: str
    read: str  # e.g. "6 min read"


@dataclass(frozen=True)
class SiteData:
    profile: Profile
    socials: list[SocialLink]
    products: list[Product]
    experience: list[Experience]
    skills: list[SkillGroup]
    education: list[Education]
    languages: list[Language]


@dataclass(frozen=True)
class Content:
    site: SiteData
    posts: list[Post] = field(default_factory=list)

    def post_by_slug(self, slug: str) -> Post | None:
        for post in self.posts:
            if post.slug == slug:
                return post
        return None
