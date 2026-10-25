import re

with open('/home/brrr/gemini_cli/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 彻底重写 _promotion_code_exists 函数
old_func_pattern = r"def _promotion_code_exists\(code\):.*?return False\n\n\ndef"
new_func = """def _promotion_code_exists(code):
    if not code:
        return False
    file_path = Path('/srv/daxa-newone/standard_promo_codes.csv')
    if not file_path.exists():
        return False
    # 使用 utf-8-sig 以兼容可能有 BOM 的 CSV 文件
    with file_path.open(encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            # 新 CSV 的表头是 'Code'，同时对两端进行去空格处理
            if (row.get('Code') or '').strip() == code.strip():
                return True
    return False


def"""

content = re.sub(old_func_pattern, new_func, content, flags=re.DOTALL)

with open('/home/brrr/gemini_cli/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
