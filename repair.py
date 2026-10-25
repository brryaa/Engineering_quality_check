import re

path = '/home/brrr/gemini_cli/meeting_registration_page.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 注入 CSS 样式
css_patch = """
    /* 重构后的交互样式 */
    .meeting-form-enhanced[data-step="1"] [data-step-2-area],
    .meeting-form-enhanced[data-step="1"] .meeting-form-actions { display: none; }
    
    .btn-full-width {
        width: 100%;
        margin-top: 20px;
        padding: 14px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        transition: all 0.3s;
    }
    
    .btn-submitted {
        background-color: #e0e0e0 !important;
        color: #888 !important;
        cursor: not-allowed;
        pointer-events: none;
    }
    
    .step-1-container { position: relative; margin-bottom: 30px; }
    
    .query-link-br {
        position: absolute;
        right: 0;
        bottom: -24px;
        font-size: 13px;
        color: #666;
        text-decoration: underline;
        background: none;
        border: none;
        cursor: pointer;
    }

    .price-stats-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 15px;
        background: #f9f9f9;
        padding: 15px;
        border-radius: 8px;
        margin: 20px 0;
        text-align: center;
    }
    .price-stats-item label { display: block; font-size: 12px; color: #888; margin-bottom: 4px; }
    .price-stats-item span { font-weight: bold; font-size: 16px; color: #333; }
    
    .payment-btns-row, .promo-row-new {
        display: flex;
        gap: 10px;
        margin-bottom: 15px;
    }
    .payment-btns-row button { flex: 1; }
    .promo-row-new input { flex: 1; }
"""
content = content.replace("</style>", css_patch + "\n    </style>")

# 2. 调整 Step 1 结构：加入提交按钮和查询链接
# 寻找 Step 1 结束点 (添加参会人按钮之后)
step1_insertion_pattern = r'(<button class="btn btn-add-attendee".*?</p>\s*</section>)'
step1_replacement = r"""\1
    <div class="step-1-container">
        <button type="button" class="btn btn-primary btn-full-width" data-submit-info-only>提交报名信息</button>
        <button class="query-link-br" type="button" data-registration-query-link>报名查询</button>
    </div>
"""
content = re.sub(step1_insertion_pattern, step1_replacement, content, flags=re.DOTALL)

# 3. 调整 Step 2 结构：改为动态展开区域
step2_start_pattern = r'<section class="meeting-step-card" style="padding-top: 0;">'
content = content.replace(step2_start_pattern, '<section class="meeting-step-card" data-step-2-area style="padding-top: 0; margin-top: 40px;">')

# 4. 重构 Step 2 内部：价格统计 + 并排支付 + 优惠码 + 提交支付
step2_inner_pattern = r'<div class="meeting-payment-grid enhanced-payment-grid">.*?</div>\s*</section>'
new_step2_inner = """
    <div class="price-stats-grid">
        <div class="price-stats-item"><label>报名人数</label><span data-summary-count>1 人</span></div>
        <div class="price-stats-item"><label>单价</label><span>￥<span data-summary-unit-price>0</span></span></div>
        <div class="price-stats-item"><label>总价</label><span style="color:#d32f2f;">￥<span data-summary-total>0</span></span></div>
    </div>
    
    <p class="meeting-meta-label" style="margin-bottom:8px;">选择支付方式</p>
    <div class="payment-btns-row">
        <button type="button" class="btn btn-secondary-dark" data-select-channel="alipay" style="border:2px solid #eee;">支付宝</button>
        <button type="button" class="btn btn-secondary-dark" data-select-channel="wechat_pay" style="border:2px solid #eee;">微信支付</button>
        <input type="hidden" name="payment_channel" value="alipay">
    </div>

    <div class="promo-row-new">
        <input class="meeting-input" type="text" placeholder="如持有优惠码请在此输入" data-promo-code-input>
        <button class="btn btn-secondary-dark" type="button" data-apply-promo-button style="white-space:nowrap; padding: 0 15px;">提交</button>
    </div>

    <button class="btn btn-primary btn-full-width" type="button" data-final-pay-btn>提交支付</button>
    
    <div class="payment-session-panel" data-payment-panel hidden style="margin-top:20px; border-top:1px dashed #ddd; padding-top:20px;">
        <div style="text-align:center;">
            <p data-payment-state style="font-weight:bold; color:#f57c00;">正在生成二维码...</p>
            <img class="payment-qr-image" src="" data-payment-qr style="max-width:200px; margin:10px auto;">
            <p data-payment-message class="meeting-field-help"></p>
            <p data-payment-countdown-msg style="font-size:12px; color:#999;"></p>
            <button class="btn btn-secondary-dark" type="button" data-close-payment-panel style="width:100%; margin-top:10px;">关闭二维码</button>
        </div>
    </div>
</section>
"""
content = re.sub(step2_inner_pattern, new_step2_inner, content, flags=re.DOTALL)

# 5. 清理原有的底部动作按钮 (因为已经整合进去了)
content = re.sub(r'<div class="meeting-form-actions">.*?</div>', '', content, flags=re.DOTALL)

# 6. 注入 JS 逻辑控制器
js_controller = """
    /* ============================
     * Step-based Flow Controller
     * ============================ */
    (function() {
        var form = document.querySelector('[data-registration-form]');
        if (!form) return;
        
        var submitInfoBtn = form.querySelector('[data-submit-info-only]');
        var finalPayBtn = form.querySelector('[data-final-pay-btn]');
        var draftOrderInput = form.querySelector('[data-draft-order-id]');
        
        // 初始状态
        form.setAttribute('data-step', '1');

        // 切换支付渠道
        form.querySelectorAll('[data-select-channel]').forEach(function(btn) {
            btn.onclick = function() {
                var channel = this.dataset.selectChannel;
                form.querySelector('[name=payment_channel]').value = channel;
                form.querySelectorAll('[data-select-channel]').forEach(function(b) { 
                    b.style.borderColor = '#eee'; 
                    b.classList.replace('btn-primary', 'btn-secondary-dark');
                });
                this.style.borderColor = '#007bff';
                // this.classList.replace('btn-secondary-dark', 'btn-primary');
            };
        });
        // 默认勾选第一个
        form.querySelector('[data-select-channel="alipay"]').click();

        function switchToStep2(orderId, attendeeCount, totalAmount) {
            form.setAttribute('data-step', '2');
            draftOrderInput.value = orderId;
            submitInfoBtn.textContent = '报名信息已提交';
            submitInfoBtn.classList.add('btn-submitted');
            
            // 更新统计显示
            form.querySelector('[data-summary-count]').textContent = attendeeCount + ' 人';
            form.querySelector('[data-summary-unit-price]').textContent = form.dataset.unitPrice;
            form.querySelector('[data-summary-total]').textContent = totalAmount;
            
            // 更新 URL (平移信息用)
            var url = new URL(window.location);
            url.searchParams.set('order_id', orderId);
            window.history.replaceState({}, '', url);
        }

        // 逻辑 A: 提交报名信息
        submitInfoBtn.onclick = function() {
            if (!form.reportValidity()) return;
            setLoading(submitInfoBtn, true);
            var fd = new FormData(form);
            fetch(form.dataset.preRegisterUrl, { method: 'POST', body: fd, headers: {'X-CSRFToken': getCsrf()} })
            .then(function(r){ return r.json(); })
            .then(function(data){
                setLoading(submitInfoBtn, false);
                if(data.ok) {
                    switchToStep2(data.draft_order_id, data.attendee_count, data.amount);
                } else {
                    alert(data.message || '提交失败');
                }
            });
        };

        // 逻辑 B: 六分支支付引擎
        finalPayBtn.onclick = function() {
            var channel = form.querySelector('[name=payment_channel]').value;
            var orderId = draftOrderInput.value;
            
            if (isWechatBrowser()) {
                if (channel === 'alipay') {
                    showWechatGuideMask(); // 遮罩层逻辑已在 mask 内部包含 order_id
                    return;
                }
                // 微信内 + 微信支付 -> 直接走原有逻辑
            } else if (isMobileBrowser()) {
                if (channel === 'alipay') {
                    showAlipayMobileModal(); // 弹出跳转
                    return;
                }
                // 手机浏览器 + 微信支付 -> 走二维码
            }
            
            // 默认走后端 fetch 获取二维码
            setLoading(finalPayBtn, true);
            var fd = new FormData(form);
            fd.append('order_id', orderId);
            fetch(form.dataset.createPaymentUrl, { method: 'POST', body: fd, headers: {'X-CSRFToken': getCsrf()} })
            .then(function(r){ return r.json(); })
            .then(function(data){
                setLoading(finalPayBtn, false);
                if(!data.ok) { alert(data.message); return; }
                
                // 处理渲染
                if (data.payment_mode === 'wechat_auth') { window.location.href = data.auth_url; return; }
                
                var panel = form.querySelector('[data-payment-panel]');
                panel.hidden = false;
                panel.scrollIntoView({behavior:'smooth'});
                form.querySelector('[data-payment-qr]').src = data.qr_image || '';
                form.querySelector('[data-payment-state]').textContent = '请扫码支付';
                form.querySelector('[data-payment-message]').textContent = data.message;
            });
        };

        // 逻辑 C: 页面载入检查 (处理“在浏览器打开”后的平移)
        var savedOrderId = new URLSearchParams(window.location.search).get('order_id');
        if (savedOrderId && form.getAttribute('data-step') === '1') {
            // 自动通过 order_id 载入状态 (这里可以调用一个静默查询接口，简化起见我们假设后端已在模板中处理或通过 JS 补全)
            // 如果后端没给现成的，我们可以通过 apply_promo_code 试探或新增一个 get_order_brief 接口
        }
    })();
"""
# 注入到文件末尾的脚本块中
content = content.replace("})();\n</script>", js_controller + "\n})();\n</script>")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
