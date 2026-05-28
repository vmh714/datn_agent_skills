import json

with open('all_skills.json', 'r', encoding='utf-8') as f:
    skills = json.load(f)

calls = ""
for s in skills:
    payload = {
        "name": s["name"],
        "description": s["description"],
        "system_prompt": s["system_prompt"],
        "toolSummary": f"Define {s['name']}",
        "toolAction": f"Defining {s['name']}"
    }
    # use json.dumps to get valid json string, then strip the surrounding {}
    json_str = json.dumps(payload)
    calls += f"\u120Fcall:default_api:define_subagent{json_str}\u1210"

with open('tool_calls.txt', 'w', encoding='utf-8') as f:
    f.write(calls)
