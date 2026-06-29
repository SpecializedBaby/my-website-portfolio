---
title: Designing Multi-Role Auth with Granular Permissions
date: 2025-12-11
tag: Backend
excerpt: JWT auth, email-link login, account reactivation, and a multi-role PostgreSQL user model with per-feature permission assignment — built to scale from day one.
---

An internal platform that several teams depend on can't ship with "admin" and "everyone
else." Sales, finance, agents, and the director each need a different slice. We built the
permission model before the features it would guard, which turned out to be the cheap order
to do it in.

## Roles group permissions; checks read permissions

The mistake to avoid is scattering `if user.role == "finance"` through the codebase. Roles
change; the things you're actually protecting don't. So code checks *permissions*, and roles
are just named bundles of them.

```python
def require(permission: str):
    async def dep(user: User = Depends(current_user)):
        if permission not in user.permissions:
            raise HTTPException(403, "forbidden")
        return user
    return dep

@router.get("/payouts", dependencies=[Depends(require("finance.read"))])
async def list_payouts(): ...
```

A user can hold more than one role, and permissions are the union. Granting a salesperson
temporary finance read access is a row, not a deploy.

## The data model

In PostgreSQL it's the familiar shape — `users`, `roles`, `permissions`, and the join tables
— with the permission set resolved at login and cached on the token's session. The
resolution query is a couple of joins; the result is small enough to carry in the JWT claims
so most requests authorize without a database round-trip.

## Auth flows that respect real life

- **Email-link login.** No password to leak or reset; a signed, short-lived token in the
  link.
- **Account reactivation.** Deactivation is reversible and audited — people leave and come
  back, and their history shouldn't be destroyed to do it.
- **JWT with short expiry + refresh.** Access tokens expire quickly; refresh is revocable, so
  removing access is immediate rather than "whenever the token expires."

## Why "from day one" mattered

Retrofitting authorization is miserable because every endpoint already assumes the caller is
allowed. Starting with `require(...)` on the very first protected route meant the 200th route
inherited the pattern for free. The permission table grew; the architecture didn't have to
change.
