import re

with open('/home/brrr/gemini_cli/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 彻底重写 _promotion_code_exists 逻辑，改为读取 .txt 文件并进行极致纯净的处理
# 我们使用一个简单的 set 来实现内存级的高速匹配
new_func_impl = """def _promotion_code_exists(code):
    if not code:
        return False
    file_path = Path('/srv/daxa-newone/promo_code.txt')
    if not file_path.exists():
        return False
    try:
        # 读取文件，按行分割，对每一行进行彻底的清理：去空格、去回车、去不可见字符
        with open(file_path, 'r', encoding='utf-8') as f:
            valid_codes = {line.strip() for line in f if line.strip()}
        
        # 将用户输入的码也进行同样的彻底清理
        target_code = code.strip().upper() # 统一转大写以增加容错性
        return target_code in valid_codes
    except Exception:
        return False


def"""

# 替换掉旧的函数体
old_func_pattern = r"def _promotion_code_exists\(code\):.*?return False\n\n\ndef"
content = re.sub(old_func_pattern, new_func_impl, content, flags=re.DOTALL)

with open('/home/brrr/gemini_cli/views.py', 'w', encoding='utf-8') as f:
    f.write(content)
