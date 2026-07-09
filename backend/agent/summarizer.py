from openai import OpenAI
import os
import json
from agent.citations import generate_citations

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def summarize(topic, sources):
    formatted = "\n\n".join([
        f"{i+1}. {s['title']}\n{s['link']}\nAbstract: {s.get('abstract') or 'N/A'}"
        for i, s in enumerate(sources)
    ])

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        messages=[
            {
                "role": "system",
                "content": "You are an elite research analyst. Return structured JSON only. "
                            "Only make claims that are directly supported by the abstract provided "
                            "for each source. Never invent facts, statistics, or findings that are "
                            "not present in the given abstracts. If a source's abstract is 'N/A', you "
                            "must return null for every field for that source - do not guess, do not "
                            "use the topic or other sources to fill in a plausible-sounding answer."
            },
            {
                "role": "user",
                "content": f"""
Topic: {topic}

Sources (numbered, in order):
{formatted}

For EACH numbered source above, in the SAME ORDER, return an object with:
- "why_it_matters": one sentence on why this specific source is relevant to the topic, grounded ONLY in its abstract
- "key_takeaway": the single most important takeaway from THIS source's abstract
- "insight": one specific insight grounded in THIS source's abstract, or null if not supported
- "trend": one specific trend grounded in THIS source's abstract, or null if not supported
- "application": one real-world application grounded in THIS source's abstract, or null if not supported

If a source's abstract above is "N/A", return null for ALL FIVE fields for that source. Do not write
a generic or inferred description when there is no abstract to base it on.

Return JSON ONLY in this exact format, with exactly {len(sources)} objects in "per_source", in the
same order as the numbered sources above:

{{
  "per_source": [
    {{
      "why_it_matters": "",
      "key_takeaway": "",
      "insight": "",
      "trend": "",
      "application": ""
    }}
  ]
}}
"""
            }
        ]
    )

    content = res.choices[0].message.content.strip()

    # Groq models sometimes wrap JSON in ```json ... ``` fences - strip if present
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    parsed = json.loads(content)
    per_source = parsed.get("per_source", [])

    sources_analysis = []
    insights = []
    trends = []
    applications = []

    # zip LLM output with our OWN verified source list by index - the title/link
    # always comes from our real search results, never from the model, so every
    # citation is guaranteed to point at an actual source we retrieved
    for i, source in enumerate(sources):
        item = per_source[i] if i < len(per_source) else {}
        has_abstract = bool((source.get("abstract") or "").strip())

        why_it_matters = item.get("why_it_matters") or ""
        key_takeaway = item.get("key_takeaway") or ""

        sources_analysis.append({
            "title": source["title"],
            "link": source["link"],
            "why_it_matters": why_it_matters,
            "key_takeaway": key_takeaway,
            "citations": generate_citations(source),
        })

        # only attach insight/trend/application if the source actually had an
        # abstract to ground it in - never let a no-abstract source contribute
        # a claim to these sections
        if has_abstract:
            if item.get("insight"):
                insights.append({"text": item["insight"], "source": source["link"]})
            if item.get("trend"):
                trends.append({"text": item["trend"], "source": source["link"]})
            if item.get("application"):
                applications.append({"text": item["application"], "source": source["link"]})

    return {
        "sources_analysis": sources_analysis,
        "insights": insights,
        "trends": trends,
        "applications": applications,
    }


def answer_followup(topic, sources, previous_summary, question):
    """Answer a follow-up question using the SAME retrieved sources from the
    original search - no new search happens. This is real RAG behavior: the
    question is grounded only in abstracts we already fetched."""
    formatted = "\n\n".join([
        f"{i+1}. {s.get('title', 'Untitled')}\n{s.get('link', '')}\nAbstract: {s.get('abstract') or 'N/A'}"
        for i, s in enumerate(sources)
    ])

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        messages=[
            {
                "role": "system",
                "content": "You are an elite research analyst answering a follow-up question. "
                            "Answer ONLY using the abstracts provided below - the same sources "
                            "already retrieved for this topic. If the abstracts don't contain "
                            "enough information to answer the question, say so honestly rather "
                            "than guessing or using outside knowledge. Return JSON only."
            },
            {
                "role": "user",
                "content": f"""
Original topic: {topic}

Sources already retrieved (numbered):
{formatted}

Follow-up question: {question}

Return JSON ONLY in this format:

{{
  "answer": "your answer, grounded only in the abstracts above",
  "supporting_sources": [1, 3]
}}

"supporting_sources" should list the numbers of the sources above that support your answer.
If none of the sources support an answer, set "answer" to explain that and use an empty list
for "supporting_sources".
"""
            }
        ]
    )

    content = res.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    parsed = json.loads(content)
    answer = parsed.get("answer", "")
    supporting_indices = parsed.get("supporting_sources", []) or []

    supporting = []
    for idx in supporting_indices:
        pos = idx - 1
        if 0 <= pos < len(sources):
            supporting.append({
                "title": sources[pos].get("title", "Untitled"),
                "link": sources[pos].get("link", "")
            })

    return {
        "answer": answer,
        "supporting_sources": supporting,
    }


def generate_digest_intro(topic, sources):
    """Generate a short 2-3 sentence intro for a weekly digest email,
    summarizing what's new this week for a topic. Lightweight - one LLM
    call, not a full per-source analysis, since this may run across many
    subscriptions on a schedule."""
    formatted = "\n".join([
        f"- {s['title']}"
        for s in sources[:8]
    ])

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.5,
        messages=[
            {
                "role": "system",
                "content": "You write short, friendly weekly research digest intros. "
                            "2-3 sentences max. No fluff, no hallucinated specifics - "
                            "just a brief orientation to what this week's sources cover."
            },
            {
                "role": "user",
                "content": f"Topic: {topic}\n\nThis week's sources:\n{formatted}\n\n"
                           f"Write a short 2-3 sentence intro for a weekly email digest "
                           f"about these sources. Plain text only, no markdown."
            }
        ]
    )
    return res.choices[0].message.content.strip()
