import re

with open('/home/brrr/gemini_cli/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update CSV path in _promotion_code_exists
content = content.replace("'/srv/daxa-newone/promotion_codes.csv'", "'/srv/daxa-newone/standard_promo_codes.csv'")

# 2. Update field name in DictReader check (The new CSV header is 'Code')
old_check = "if row.get('promotion_code') == code:"
new_check = "if row.get('Code') == code:"
content = content.replace(old_check, new_check)

# 3. Remove the 15-character length check in apply_promo_code
content = re.sub(r"if len\(promo_code\) != 15:\s+return _json_error\('.*?'\)", "# Length check removed", content)

with open('/home/brrr/gemini_cli/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
