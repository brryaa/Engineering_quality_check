import re

with open('/home/brrr/gemini_cli/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 将错误的宿主机绝对路径修正为容器内的 BASE_DIR 路径
old_path = "Path('/srv/daxa-newone/promo_code.txt')"
new_path = "BASE_DIR / 'promo_code.txt'"
content = content.replace(old_path, new_path)

with open('/home/brrr/gemini_cli/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
