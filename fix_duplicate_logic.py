import re

file_path = 'backend/main.py'
with open(file_path, 'r') as f:
    content = f.read()

# Pattern for the duplicated block left over
duplicate_pattern = r'return result\n\n    # Compute investment score.*?datetime\.now\(timezone\.utc\)\.isoformat\(\) # Placeholder for first_seen_at if not available\n    \)'
replacement = 'return result'

new_content = re.sub(duplicate_pattern, replacement, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(new_content)
