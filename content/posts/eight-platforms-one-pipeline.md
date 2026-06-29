---
title: From 8 Platforms to One Lead Pipeline
date: 2026-01-20
tag: Integrations
excerpt: Unifying Idealista, Booking.com, Airbnb, Meta Lead Ads and more into a single event-driven pipeline with two-way property sync — the CRM as the source of truth.
---

Leads came from everywhere: Idealista, Booking.com, Airbnb, Meta Lead Ads, web forms, and a
few inboxes nobody wanted to admit to. Eight surfaces, eight formats, eight ways to drop a
lead on the floor. We collapsed them into one pipeline.

## Normalize at the edge, not in the core

Each integration is a thin adapter whose only job is to turn a provider's payload into one
canonical `Lead` event and hand it to the pipeline. The core never learns a provider's
quirks.

```python
@router.post("/webhooks/{provider}")
async def ingest(provider: str, payload: dict):
    adapter = ADAPTERS[provider]
    event = adapter.to_lead_event(payload)   # provider-specific → canonical
    await pipeline.publish(event)            # everything past here is provider-agnostic
    return {"ok": True}
```

Adding a ninth source later was writing one `to_lead_event` function — not touching dedup,
routing, or reporting.

## Two-way property sync

Listings flow the other direction: the CRM is the source of truth for a property, and
changes fan out to the channels that advertise it. The hard part isn't pushing updates — it's
deciding who wins on conflict. We made the CRM authoritative for descriptive fields and let
each channel own its own availability calendar, which removed almost all of the conflicts
that two-way sync usually creates.

## The pipeline is event-driven for a reason

Behind the webhook is a message broker, not a synchronous chain. That buys three things:

- **Backpressure.** A burst from a Meta campaign queues instead of knocking over the API.
- **Retries.** A flaky provider webhook is retried without a human noticing.
- **Fan-out.** Dedup, scoring, agent assignment, and notification all subscribe to the same
  `lead.created` event independently.

The headline metric was that lead capture went from "mostly" to "essentially all, within
seconds." The architectural point is quieter: when every source becomes the same event, the
interesting work — scoring, routing, follow-up — only has to be built once.
