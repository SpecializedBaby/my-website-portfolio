---
title: RAG-Powered Task Assignment for Construction Teams
date: 2025-04-22
tag: AI
excerpt: How I built a RAG assistant with OpenAI + LangChain to recommend task assignments and compute material quantities — cutting manual planning overhead for project managers.
---

Project managers on a construction firm spent hours each week answering two questions: who
should do this task, and how much material does it need? Both answers lived in documents and
past projects nobody had time to read. A retrieval-augmented assistant turned that tacit
knowledge into a suggestion.

## Retrieval first, generation second

The value wasn't the language model — it was the retrieval. The assistant grounds every
answer in the firm's own data: past task assignments, worker skill records, supplier
specs, and material tables. The model's job is to reason over retrieved facts, not to recall
them.

```python
docs = retriever.get_relevant_documents(query)      # firm's own knowledge
context = format_context(docs)
answer = llm.invoke(ASSIGNMENT_PROMPT.format(
    context=context, task=task_description,
))
```

If retrieval returns nothing relevant, the assistant says so rather than inventing a
plausible-sounding crew assignment. For a planning tool, a confident wrong answer is worse
than an honest "not enough information."

## Two jobs, one pattern

- **Task assignment.** Given a task, retrieve similar past tasks and the skills they
  required, then recommend workers whose records match — with the reasoning shown so the PM
  stays in control.
- **Material quantities.** Given a job spec, retrieve the relevant material rules and compute
  quantities. The arithmetic is done in code; the model's role is to pick the right rule and
  extract the inputs, not to do the math.

## Keeping it trustworthy

The assistant recommends; the project manager decides. Every suggestion carries its sources,
so a PM can check the past project a recommendation came from. That transparency was what
moved it from "neat demo" to "thing people actually use" — they trusted it because they could
audit it.

The overhead it removed wasn't decision-making. It was the search — the half hour of digging
through old projects before the decision could even start.
