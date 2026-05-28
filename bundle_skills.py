import os, json, re

skills = []
root = r'd:\datn\datn_agent_skills\.agents\skills'

for r, d, files in os.walk(root):
    for f in files:
        if f == 'SKILL.md':
            filepath = os.path.join(r, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                name_match = re.search(r'name:\s*(.+)', content)
                desc_match = re.search(r'description:\s*(.+)', content)
                if name_match and desc_match:
                    name = name_match.group(1).strip().strip('"\'')
                    desc = desc_match.group(1).strip().strip('"\'')
                    skills.append({'name': name, 'description': desc, 'system_prompt': content})

with open('all_skills.json', 'w', encoding='utf-8') as f:
    json.dump(skills, f, indent=2)
