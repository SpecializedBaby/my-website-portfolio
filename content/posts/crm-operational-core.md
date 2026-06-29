---
title: Building a CRM That Became the Operational Core
date: 2026-03-09
tag: Systems
excerpt: Architecting a production CRM from scratch — lead intake, deal management, property listings, and owner financial reporting — now the single source of truth for the whole company.
---

We didn't set out to build "a CRM." We set out to stop losing leads and stop reconciling
spreadsheets. The system that grew out of those two problems became the place the company
runs from.

## Start from the events, not the screens

The first design decision was to model the business as a stream of events — a lead arrived,
a deal advanced, a reservation was confirmed, an owner was paid — rather than as a set of
CRUD screens. Everything downstream (reporting, automation, audit) reads from that event
history.

```text
lead.created → deal.opened → deal.won → reservation.confirmed
            → agent.assigned → owner.payout.calculated → report.generated
```

Because each transition is a recorded fact, the monthly owner report isn't a query someone
runs and double-checks — it's a fold over events that already happened.

## One source of truth, many consumers

Lead intake, deal management, property listings, and owner financial reporting all live in
the same domain model. A property is the same entity whether it's being listed, booked, or
reported on. That sounds obvious, but it's exactly what fragmented tooling gets wrong: the
listing system and the finance system each keep their own half-truth and someone spends
Friday reconciling them.

## What "operational core" actually demanded

- **Auditability.** Every state change is attributable — who, when, from what. This is what
  let the team trust the numbers enough to delete the spreadsheets.
- **Boring data integrity.** Foreign keys, constraints, and transactions over clever
  denormalization. The CRM is allowed to be slow before it is allowed to be wrong.
- **Room for automation.** Because state changes are events, automations subscribe instead
  of poll. Adding "notify the owner when payout is computed" was a subscriber, not a
  migration.

The CRM earned the title "operational core" the day people stopped keeping a private
spreadsheet "just in case." That's the real acceptance test for an internal platform.
