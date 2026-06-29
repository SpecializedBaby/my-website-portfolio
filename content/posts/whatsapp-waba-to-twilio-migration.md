---
title: Migrating WhatsApp from Meta WABA to Twilio in 3 Days
date: 2026-05-14
tag: Architecture
excerpt: When a billing-infrastructure failure threatened our entire lead flow, we executed a live migration from Facebook WABA to Twilio in 72 hours — with zero permanent disruption. Here is how we de-risked it.
---

WhatsApp was our highest-intent channel. When a billing failure on the Meta side froze our
WhatsApp Business Account, every inbound lead that preferred WhatsApp went dark. We couldn't
wait out a support queue — we migrated the channel to Twilio in three days, live, without
losing a conversation.

## The constraint that shaped everything

The CRM never talked to Meta directly. Every messaging provider sat behind a single internal
interface:

```python
class MessagingProvider(Protocol):
    async def send_text(self, to: str, body: str) -> MessageId: ...
    async def send_template(self, to: str, template: str, vars: dict) -> MessageId: ...

async def handle_inbound(event: InboundMessage) -> None:
    lead = await leads.upsert_from_contact(event.from_)
    await timeline.record(lead.id, event)
    await router.dispatch(lead, event)
```

Because the rest of the system only knew that abstraction, swapping providers was a
matter of writing a new adapter and a new webhook translator — not touching business logic.

## De-risking the cutover

We ran both providers in parallel behind a feature flag keyed per phone number. New
conversations were routed to Twilio first; in-flight Meta threads were allowed to drain.
A normalization layer mapped both providers' webhook payloads into one internal
`InboundMessage` shape, so the timeline and router never knew which provider a message came
from.

The template library was the slow part — every WhatsApp template has to be re-approved by
the new provider. We submitted them on day one, in parallel with the adapter work, so
approval latency overlapped the build instead of following it.

## What made it survivable

- **A provider seam that already existed.** The migration was an adapter, not a rewrite.
- **Idempotent inbound handling.** Replays and duplicate webhooks during the cutover were
  harmless because `upsert_from_contact` and message dedup were idempotent by design.
- **Parallel run, not a big-bang switch.** We never had a moment where both old and new were
  off.

The lesson wasn't about WhatsApp or Twilio specifically. It was that the cost of a vendor
emergency is set months earlier — by whether you put a seam between your business logic and
the vendor.
