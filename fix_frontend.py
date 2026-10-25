import re

with open('/home/brrr/gemini_cli/meeting_registration_page.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update placeholder and help text
content = content.replace('placeholder="请输入15位优惠码"', 'placeholder="请输入优惠码"')
content = content.replace('如持有15位优惠码，可直接免付款完成报名。', '如持有优惠码请在此输入')

# 2. Update JavaScript length check (in multiple places)
content = re.sub(r"if \(promoCode\.length !== 15\) \{ showFeedback\('.*?', true\); return; \}", "if (promoCode.length === 0) { showFeedback('请输入优惠码。', true); return; }", content)
content = re.sub(r"if \(promoCode\.length !== 15\) \{ alert\('.*?'\); return; \}", "if (promoCode.length === 0) { alert('请输入优惠码'); return; }", content)

# 3. Handle modal specific code
content = content.replace('maxlength="15"', '')

with open('/home/brrr/gemini_cli/meeting_registration_page.html', 'w', encoding='utf-8') as f:
    f.write(content)
