from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize(topic, sources):
    formatted = "\n\n".join([
        f"{i+1}. {s['title']}\n{s['link']}"
        for i, s in enumerate(sources)
    ])

    res = client.chat.completions.create(
        model="gpt-4o-mini",
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

    return json.loads(res.choices[0].message.content)