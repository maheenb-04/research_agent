from openai import OpenAI
import os
import json

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def summarize(topic, sources):
    formatted = "\n\n".join([
        f"{i+1}. {s['title']}\n{s['link']}\nAbstract: {s.get('abstract') or 'N/A'}"
        for i, s in enumerate(sources)
    ])

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.6,
        messages=[
            {
                "role": "system",
                "content": "You are an elite research analyst. Return structured JSON only."
            },
            {
                "role": "user",
                "content": f"""
Topic: {topic}

Sources:
{formatted}

Return JSON ONLY in this format:

{{
  "sources_analysis": [
    {{
      "title": "",
      "link": "",
      "why_it_matters": "",
      "key_takeaway": ""
    }}
  ],
  "insights": [],
  "trends": [],
  "applications": []
}}
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

    return json.loads(content)
