import csv
import json
import logging
import random
import string
import uuid
from pathlib import Path
from urllib.parse import urlencode, quote
from urllib.request import urlopen
from decimal import Decimal

from django.conf import settings
from django.core import signing
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import MeetingRegistrationOrderForm, PreRegistrationForm, build_participants
from .models import (
    MeetingParticipant,
    MeetingRegistrationOrder,
    MeetingRegistrationPage,
    SmsVerificationCode,
    _get_client_ip,
)
from .notifications import send_registration_email, send_sms_verification
from .payments import PaymentConfigurationError, PaymentGatewayError, create_payment, query_payment


logger = logging.getLogger(__name__)


def _json_error(message, *, status=400, errors=None):
    payload = {'ok': False, 'message': message}
    if errors:
        payload['errors'] = errors
    return JsonResponse(payload, status=status)


def _get_page(page_id):
    return get_object_or_404(MeetingRegistrationPage, pk=page_id)


def _get_order(page, public_id):
    return get_object_or_404(page.registration_orders, public_id=public_id)


def _manual_qr_payload(order, *, amount, include_totals=False, request=None):
    is_mobile = _is_mobile_browser(request) if request else False
    if order.payment_channel == 'alipay':
        if is_mobile:
            qr_image = ''
            show_qr = False
            action_url = 'https://qr.alipay.com/45t111548ewnriuz0p9xm0d'
            action_label = '点击打开支付宝付款'
            action_hint = '若未自动跳转支付宝则点右上角... 选择默认浏览器打开'
            message = '请点击下方按钮打开支付宝完成付款。'
            countdown_seconds = 120
        else:
            qr_image = 'https://daxa.ltd/media/images/alipay_photo_2026-04-25_23-48-47.original.jpg'
            show_qr = True
            action_url = ''
            action_label = ''
            action_hint = ''
            message = '请使用支付宝扫码付款。'
            countdown_seconds = 120
    else:
        qr_image = 'https://daxa.ltd/media/images/photo_2026-04-21_13-45-23.original.jpg'
        show_qr = True
        action_url = ''
        action_label = ''
        action_hint = ''
        message = '微信支付接口暂时不可用，已切换为人工扫码确认。'
        countdown_seconds = 180 if not is_mobile else 120
    payload = {
        'ok': True,
        'draft_order_id': order.public_id,
        'amount': amount,
        'payment_mode': 'manual_qr',
        'qr_image': qr_image,
        'qr_payload': 'static',
        'show_qr': show_qr,
        'action_url': action_url,
        'action_label': action_label,
        'action_hint': action_hint,
        'countdown_seconds': countdown_seconds,
        'message': message,
    }
    if include_totals:
        payload.update({
            'total_amount': order.total_amount_display,
            'paid_amount': order.paid_amount_display,
            'outstanding_amount': order.outstanding_amount_display,
        })
    else:
        payload.update({
            'attendee_count': order.attendee_count,
            'payment_channel': order.get_payment_channel_display(),
        })
    return payload


def _daily_counter_key(scope, value):
    return f'meetings:sms:{scope}:{timezone.localdate().isoformat()}:{value}'


def _seconds_until_day_end():
    now = timezone.localtime()
    next_day = (now + timezone.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(int((next_day - now).total_seconds()), 1)


def _counter_value(key):
    return int(cache.get(key, 0) or 0)


def _bump_daily_counter(key):
    timeout = _seconds_until_day_end()
    added = cache.add(key, 1, timeout=timeout)
    if not added:
        try:
            cache.incr(key)
        except ValueError:
            cache.set(key, 1, timeout=timeout)


def _get_query_cookie_id(request):
    cookie_name = settings.MEETING_SMS_COOKIE_NAME
    cookie_id = (request.COOKIES.get(cookie_name) or '').strip()
    created = False
    if not cookie_id:
        cookie_id = uuid.uuid4().hex
        created = True
    return cookie_id, created


def _set_order_cookie(response, order_id):
    response.set_cookie(
        'mr_order_id',
        order_id,
        max_age=90 * 86400,
        httponly=True,
        samesite='Lax',
        secure=settings.SESSION_COOKIE_SECURE,
    )
    return response


def _make_query_bind_token(order_ids):
    return signing.dumps({'order_ids': list(order_ids)}, salt='meeting-query-bind')


def _read_query_bind_token(token, *, max_age=600):
    return signing.loads(token, salt='meeting-query-bind', max_age=max_age)


def _promotion_code_exists(code):
    if not code:
        return False
    file_path = settings.BASE_DIR / 'promo_code.txt'
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


def _finalize_paid_order(order):
    now = timezone.now()
    order.payment_status = MeetingRegistrationOrder.PaymentStatus.PAID
    order.paid_amount = order.total_amount
    order.paid_at = now
    order.order_status = MeetingRegistrationOrder.OrderStatus.SUBMITTED
    if not order.submitted_at:
        order.submitted_at = now
    order.save(update_fields=['payment_status', 'paid_amount', 'paid_at', 'order_status', 'submitted_at', 'updated_at'])
    send_registration_email(order, 'paid')
    response = JsonResponse({
        'ok': True,
        'redirect_url': f'{order.page.url}?submitted=1&order={order.public_id}',
        'message': order.page.success_message,
    })
    return _set_order_cookie(response, order.public_id)


def _payment_base_url():
    config = settings.MEETING_PAYMENT_CONFIG
    return (config.get('base_url') or settings.WAGTAILADMIN_BASE_URL).rstrip('/')


def _is_wechat_browser(request):
    return 'MicroMessenger' in (request.META.get('HTTP_USER_AGENT') or '')


def _is_mobile_browser(request):
    ua = (request.META.get('HTTP_USER_AGENT') or '').lower()
    return any(token in ua for token in ['iphone', 'android', 'mobile', 'ipad'])

def _alipay_client():
    from .payments import _alipay_client as payment_alipay_client
    return payment_alipay_client()


def _alipay_payment_payload(request, order, *, include_totals=False):
    mode = 'wap' if _is_mobile_browser(request) else 'page'
    payment = _manual_qr_payload(order, amount=order.outstanding_amount_display, request=request)
    order.payment_status = MeetingRegistrationOrder.PaymentStatus.PENDING
    order.payment_response = payment.get('raw', {})
    order.save(update_fields=['payment_status', 'payment_response', 'updated_at'])
    payload = {
        'ok': True,
        'draft_order_id': order.public_id,
        'amount': order.outstanding_amount_display if include_totals else order.total_amount_display,
        'attendee_count': order.attendee_count,
        'payment_mode': payment['payment_mode'],
        'action_url': payment['action_url'],
        'message': '正在跳转支付宝。',
    }
    if _is_wechat_browser(request):
        payload['payment_mode'] = 'alipay_external'
        payload['message'] = '请点击按钮后在默认浏览器中打开支付宝完成付款。'
        payload['action_hint'] = '点击右上角... 选择默认浏览器打开'
    if include_totals:
        payload.update({
            'total_amount': order.total_amount_display,
            'paid_amount': order.paid_amount_display,
            'outstanding_amount': order.outstanding_amount_display,
        })
    return payload


def _alipay_redirect_response(order):
    response = redirect(f'{order.page.url}?submitted=1&order={order.public_id}')
    return _set_order_cookie(response, order.public_id)


def _make_wechat_oauth_state(order, resume_kind):
    return signing.dumps({'order_id': order.public_id, 'resume_kind': resume_kind}, salt='meeting-wechat-oauth')


def _read_wechat_oauth_state(state):
    return signing.loads(state, salt='meeting-wechat-oauth', max_age=1800)


def _build_wechat_oauth_url(order, resume_kind):
    config = settings.MEETING_PAYMENT_CONFIG
    appid = config.get('wechat_appid')
    callback_url = f"{_payment_base_url()}/conference/api/payment/wechat-auth-callback/"
    query = urlencode({
        'appid': appid,
        'redirect_uri': callback_url,
        'response_type': 'code',
        'scope': 'snsapi_base',
        'state': _make_wechat_oauth_state(order, resume_kind),
    })
    return f"https://open.weixin.qq.com/connect/oauth2/authorize?{query}#wechat_redirect"


def _exchange_wechat_oauth_code(code):
    config = settings.MEETING_PAYMENT_CONFIG
    query = urlencode({
        'appid': config.get('wechat_appid'),
        'secret': config.get('wechat_appsecret'),
        'code': code,
        'grant_type': 'authorization_code',
    })
    with urlopen(f"https://api.weixin.qq.com/sns/oauth2/access_token?{query}") as response:
        payload = json.loads(response.read().decode('utf-8'))
    openid = payload.get('openid', '')
    if not openid:
        raise PaymentGatewayError(payload.get('errmsg') or '微信授权未返回 openid。')
    return openid


def _mark_order_paid(order, *, amount=None, trade_no='', raw=None):
    now = timezone.now()
    paid_amount = amount if amount is not None else order.outstanding_amount
    order.paid_amount = min(order.total_amount, order.paid_amount + paid_amount)
    order.payment_provider_trade_no = trade_no or order.payment_provider_trade_no
    if raw is not None:
        order.payment_response = raw
    order.payment_checked_at = now
    order.paid_at = now
    order.payment_status = (
        MeetingRegistrationOrder.PaymentStatus.PAID
        if order.paid_amount >= order.total_amount
        else MeetingRegistrationOrder.PaymentStatus.PENDING
    )
    if order.paid_amount >= order.total_amount:
        order.order_status = MeetingRegistrationOrder.OrderStatus.SUBMITTED
        if not order.submitted_at:
            order.submitted_at = now
    update_fields = [
        'paid_amount', 'payment_provider_trade_no', 'payment_response',
        'payment_checked_at', 'paid_at', 'payment_status', 'updated_at'
    ]
    if order.paid_amount >= order.total_amount:
        update_fields.extend(['order_status', 'submitted_at'])
    order.save(update_fields=update_fields)
    return order


def _build_mobile_wechat_payment_response(request, order, *, resume_kind):
    if not settings.MEETING_PAYMENT_CONFIG.get('wechat_public_key_id'):
        return None
    client_ip = _get_client_ip(request) or '127.0.0.1'
    if _is_wechat_browser(request):
        openid = request.session.get('wechat_openid', '')
        if not openid:
            return {
                'ok': True,
                'draft_order_id': order.public_id,
                'amount': order.outstanding_amount_display,
                'payment_mode': 'wechat_auth',
                'auth_url': _build_wechat_oauth_url(order, resume_kind),
                'message': '正在跳转微信授权。',
            }
        payment = create_payment(order, wechat_mode='jsapi', openid=openid, client_ip=client_ip)
        order.payment_status = MeetingRegistrationOrder.PaymentStatus.PENDING
        order.payment_response = payment.get('raw', {})
        order.save(update_fields=['payment_status', 'payment_response', 'updated_at'])
        return {
            'ok': True,
            'draft_order_id': order.public_id,
            'amount': order.outstanding_amount_display,
            'attendee_count': order.attendee_count,
            'payment_mode': 'wechat_jsapi',
            'jsapi_params': payment['jsapi_params'],
            'message': '正在调起微信支付。',
        }
    if _is_mobile_browser(request):
        payment = create_payment(order, wechat_mode='h5', client_ip=client_ip)
        order.payment_status = MeetingRegistrationOrder.PaymentStatus.PENDING
        order.payment_response = payment.get('raw', {})
        order.save(update_fields=['payment_status', 'payment_response', 'updated_at'])
        return {
            'ok': True,
            'draft_order_id': order.public_id,
            'amount': order.outstanding_amount_display,
            'attendee_count': order.attendee_count,
            'payment_mode': 'wechat_h5',
            'h5_url': payment['h5_url'],
            'message': '正在跳转微信支付。',
        }
    return None


def _apply_order_payload(order, page, cleaned_data, participants, request=None):
    attendee_count = len(participants)
    order.page = page
    order.registration_type = 'group' if attendee_count >= 2 else 'single'
    order.attendee_count = attendee_count
    # Derive contact info from first participant
    first = participants[0] if participants else {}
    order.organization = first.get('organization', '')
    order.contact_name = first.get('full_name', '')
    order.contact_phone = first.get('phone_number', '')
    order.contact_email = first.get('email', '')
    order.notes = ''
    order.payment_channel = cleaned_data.get('payment_channel', '')
    order.unit_price = page.ticket_price
    order.total_amount = page.ticket_price * Decimal(attendee_count)
    order.order_status = MeetingRegistrationOrder.OrderStatus.DRAFT
    if order.payment_status != MeetingRegistrationOrder.PaymentStatus.PAID:
        order.payment_status = MeetingRegistrationOrder.PaymentStatus.UNPAID
        order.payment_provider_trade_no = ''
        order.payment_qr_payload = ''
        order.payment_response = {}
        order.payment_checked_at = None
        order.paid_at = None
    if request:
        order.client_ip = _get_client_ip(request)
    order.save()
    order.participants.all().delete()
    for index, participant in enumerate(participants, start=1):
        MeetingParticipant.objects.create(
            order=order,
            sort_order=index,
            full_name=participant['full_name'],
            phone_number=participant['phone_number'],
            email=participant.get('email', ''),
            department=participant.get('department', ''),
            job_title=participant.get('job_title', ''),
            organization=participant.get('organization', ''),
            invoice_tax_number=participant.get('invoice_tax_number', ''),
            invoice_title_choice=participant.get('invoice_title_choice', 'same_as_org'),
            notes=participant.get('notes', ''),
            avatar_photo=participant.get('avatar_photo'),
        )
    return order


def _validate_participants(request, attendee_count, page):
    """Shared validation for participants."""
    participants, participant_errors = build_participants(request.POST, request.FILES, attendee_count)
    if participant_errors:
        return None, _json_error('请补全参会人信息。', errors=participant_errors)
    max_group_size = max(page.max_group_size, page.min_group_size, 2)
    if len(participants) > max_group_size:
        return None, _json_error(f'当前页面最多支持 {max_group_size} 位集体报名。')
    return participants, None


@require_POST
def create_payment_session(request):
    form = MeetingRegistrationOrderForm(request.POST)
    if not form.is_valid():
        return _json_error('请先完整填写报名信息。', errors=form.errors.get_json_data())
    page = _get_page(form.cleaned_data['page_id'])

    participants, error_resp = _validate_participants(request, form.cleaned_data['attendee_count'], page)
    if error_resp:
        return error_resp

    draft_order_id = form.cleaned_data.get('draft_order_id')
    if draft_order_id:
        order = _get_order(page, draft_order_id)
        if order.order_status == MeetingRegistrationOrder.OrderStatus.SUBMITTED:
            return _json_error('该订单已提交，不能重复发起支付。')
    else:
        order = MeetingRegistrationOrder(page=page)

    order = _apply_order_payload(order, page, form.cleaned_data, participants, request=request)
    if order.payment_channel == 'wechat_pay':
        try:
            mobile_payload = _build_mobile_wechat_payment_response(request, order, resume_kind='create')
        except PaymentConfigurationError:
            mobile_payload = None
        except PaymentGatewayError as exc:
            logger.warning(
                'Falling back to manual QR during create_payment_session: order_id=%s out_trade_no=%s reason=%s',
                order.public_id,
                order.out_trade_no,
                exc,
            )
            mobile_payload = None
        if mobile_payload:
            return JsonResponse(mobile_payload)

    order.payment_status = MeetingRegistrationOrder.PaymentStatus.PENDING
    order.payment_qr_payload = 'static'
    order.payment_response = {'manual': True}
    order.save(update_fields=['payment_status', 'payment_qr_payload', 'payment_response', 'updated_at'])
    return JsonResponse(_manual_qr_payload(order, amount=order.total_amount_display, request=request))


@require_POST
def check_payment_status(request):
    page = _get_page(request.POST.get('page_id'))
    order = _get_order(page, request.POST.get('draft_order_id', ''))
    try:
        payment_payload = query_payment(order)
    except PaymentConfigurationError as exc:
        return _json_error(str(exc), status=503)
    except PaymentGatewayError as exc:
        return _json_error(str(exc), status=502)

    order.payment_checked_at = timezone.now()
    order.payment_response = payment_payload['raw']
    order.payment_provider_trade_no = payment_payload.get('trade_no', '')
    if payment_payload['paid']:
        order.payment_status = MeetingRegistrationOrder.PaymentStatus.PAID
        order.paid_amount = order.total_amount
        order.paid_at = timezone.now()
    else:
        order.payment_status = MeetingRegistrationOrder.PaymentStatus.PENDING
    order.save(update_fields=['payment_checked_at', 'payment_response', 'payment_provider_trade_no', 'payment_status', 'paid_amount', 'paid_at', 'updated_at'])
    return JsonResponse(
        {
            'ok': True,
            'paid': payment_payload['paid'],
            'status_text': payment_payload['status_text'],
            'message': '支付已确认，可以提交报名。' if payment_payload['paid'] else '暂未查询到支付成功，请完成支付后再次核验。',
        }
    )


@require_POST
def submit_registration_order(request):
    page = _get_page(request.POST.get('page_id'))
    order = _get_order(page, request.POST.get('draft_order_id', ''))
    if order.payment_status != MeetingRegistrationOrder.PaymentStatus.PAID:
        return _json_error('请先完成支付核验，再提交报名。')
    if order.order_status != MeetingRegistrationOrder.OrderStatus.SUBMITTED:
        order.order_status = MeetingRegistrationOrder.OrderStatus.SUBMITTED
        order.submitted_at = timezone.now()
        order.save(update_fields=['order_status', 'submitted_at', 'updated_at'])
    # Send confirmation email (placeholder)
    send_registration_email(order, 'paid')
    response = JsonResponse(
        {
            'ok': True,
            'redirect_url': f'{page.url}?submitted=1&order={order.public_id}',
            'message': page.success_message,
        }
    )
    return _set_order_cookie(response, order.public_id)


@require_POST
def pre_register(request):
    """Submit a pre-registration (without payment)."""
    form = PreRegistrationForm(request.POST)
    if not form.is_valid():
        return _json_error('请先完整填写报名信息。', errors=form.errors.get_json_data())
    page = _get_page(form.cleaned_data['page_id'])

    participants, error_resp = _validate_participants(request, form.cleaned_data['attendee_count'], page)
    if error_resp:
        return error_resp

    draft_order_id = form.cleaned_data.get('draft_order_id')
    if draft_order_id:
        order = _get_order(page, draft_order_id)
        if order.order_status in (MeetingRegistrationOrder.OrderStatus.SUBMITTED, MeetingRegistrationOrder.OrderStatus.PRE_REGISTERED):
            return _json_error('该订单已提交，不能重复操作。')
    else:
        order = MeetingRegistrationOrder(page=page)

    # Build order without payment channel
    cleaned = form.cleaned_data.copy()
    cleaned['payment_channel'] = ''
    order = _apply_order_payload(order, page, cleaned, participants, request=request)
    order.order_status = MeetingRegistrationOrder.OrderStatus.PRE_REGISTERED
    order.submitted_at = timezone.now()
    order.save(update_fields=['order_status', 'submitted_at', 'updated_at'])

    # Send pre-registration email (placeholder)
    send_registration_email(order, 'pre_registered')

    response = JsonResponse(
        {
            'ok': True,
            'redirect_url': f'{page.url}?pre_registered=1&order={order.public_id}',
            'message': '预报名成功！会务组将通过邮件或电话与您联系。',
        }
    )
    return _set_order_cookie(response, order.public_id)


@require_POST
def send_query_code(request):
    """Send an SMS verification code for registration query."""
    phone = (request.POST.get('phone_number') or '').strip()
    if not phone:
        return _json_error('请输入手机号。')

    client_ip = _get_client_ip(request) or 'unknown'
    cookie_id, _ = _get_query_cookie_id(request)
    phone_key = _daily_counter_key('phone', phone)
    ip_key = _daily_counter_key('ip', client_ip)
    cookie_key = _daily_counter_key('cookie', cookie_id)

    if _counter_value(phone_key) >= settings.MEETING_SMS_PHONE_DAILY_LIMIT:
        return _json_error('该手机号今日验证码发送次数已达上限，请明日再试。', status=429)
    if _counter_value(ip_key) >= settings.MEETING_SMS_IP_DAILY_LIMIT:
        return _json_error('当前网络今日验证码发送次数已达上限，请明日再试。', status=429)
    if _counter_value(cookie_key) >= settings.MEETING_SMS_COOKIE_DAILY_LIMIT:
        return _json_error('当前设备今日验证码发送次数已达上限，请明日再试。', status=429)

    exists = MeetingParticipant.objects.filter(
        phone_number=phone,
        order__order_status__in=[
            MeetingRegistrationOrder.OrderStatus.SUBMITTED,
            MeetingRegistrationOrder.OrderStatus.PRE_REGISTERED,
        ],
    ).exists()
    if not exists:
        return _json_error('未找到该手机号的报名记录。')

    code = ''.join(random.choices(string.digits, k=6))
    SmsVerificationCode.objects.create(phone_number=phone, code=code)

    try:
        send_sms_verification(phone, code)
    except Exception as exc:
        return _json_error(str(exc), status=503)

    _bump_daily_counter(phone_key)
    _bump_daily_counter(ip_key)
    _bump_daily_counter(cookie_key)

    response = JsonResponse({'ok': True, 'message': '验证码已发送，请查收短信。'})
    response.set_cookie(
        settings.MEETING_SMS_COOKIE_NAME,
        cookie_id,
        max_age=30 * 86400,
        httponly=True,
        samesite='Lax',
        secure=settings.SESSION_COOKIE_SECURE,
    )
    return response


@require_POST
def verify_and_query(request):
    """Verify SMS code and return registration info."""
    phone = (request.POST.get('phone_number') or '').strip()
    code = (request.POST.get('code') or '').strip()
    if not phone or not code:
        return _json_error('请输入手机号和验证码。')

    cutoff = timezone.now() - timezone.timedelta(minutes=10)
    sms = SmsVerificationCode.objects.filter(
        phone_number=phone,
        code=code,
        used=False,
        created_at__gte=cutoff,
    ).order_by('-created_at').first()

    if not sms:
        return _json_error('验证码无效或已过期，请重试。')

    sms.used = True
    sms.save(update_fields=['used'])

    participants = MeetingParticipant.objects.filter(
        phone_number=phone,
        order__order_status__in=[
            MeetingRegistrationOrder.OrderStatus.SUBMITTED,
            MeetingRegistrationOrder.OrderStatus.PRE_REGISTERED,
        ],
    ).select_related('order', 'order__page').order_by('-order__submitted_at', '-order__id', 'id')

    results = []
    seen_order_ids = set()
    matched_orders = []
    for p in participants:
        if p.order.public_id in seen_order_ids:
            continue
        seen_order_ids.add(p.order.public_id)
        matched_orders.append(p.order)
        results.append({
            'order_id': p.order.public_id,
            'order_status': p.order.get_order_status_display(),
            'payment_status': p.order.get_payment_status_display(),
            'full_name': p.full_name,
            'organization': p.organization,
            'email': p.email,
            'attendee_count': p.order.attendee_count,
            'total_amount': p.order.total_amount_display,
            'submitted_at': p.order.submitted_at.isoformat() if p.order.submitted_at else '',
        })

    if len(matched_orders) == 1:
        order = matched_orders[0]
        response = JsonResponse({
            'ok': True,
            'registrations': results,
            'bound_order_id': order.public_id,
            'redirect_url': order.page.url,
            'message': '已识别您的报名信息，正在进入报名状态。',
        })
        return _set_order_cookie(response, order.public_id)

    payload = {'ok': True, 'registrations': results}
    if matched_orders:
        payload['bind_token'] = _make_query_bind_token([order.public_id for order in matched_orders])
    return JsonResponse(payload)


@require_POST
def bind_query_order(request):
    order_id = (request.POST.get('order_id') or '').strip()
    bind_token = (request.POST.get('bind_token') or '').strip()
    if not order_id or not bind_token:
        return _json_error('缺少报名绑定参数。')

    try:
        payload = _read_query_bind_token(bind_token)
    except signing.BadSignature:
        return _json_error('查询状态已失效，请重新验证手机号。', status=400)
    except signing.SignatureExpired:
        return _json_error('查询状态已过期，请重新验证手机号。', status=400)

    allowed_order_ids = set(payload.get('order_ids') or [])
    if order_id not in allowed_order_ids:
        return _json_error('该报名记录不在当前查询结果中。', status=403)

    order = MeetingRegistrationOrder.objects.filter(
        public_id=order_id,
        order_status__in=[
            MeetingRegistrationOrder.OrderStatus.SUBMITTED,
            MeetingRegistrationOrder.OrderStatus.PRE_REGISTERED,
        ],
    ).select_related('page').first()
    if not order:
        return _json_error('报名记录不存在或状态不可用。', status=404)

    response = JsonResponse({
        'ok': True,
        'order_id': order.public_id,
        'redirect_url': order.page.url,
        'message': '已进入该报名记录。',
    })
    return _set_order_cookie(response, order.public_id)


@require_POST
def add_participant(request):
    """Add participants to an existing order."""
    page = _get_page(request.POST.get('page_id'))
    order_id = request.POST.get('order_id', '')
    order = _get_order(page, order_id)

    if order.order_status not in (
        MeetingRegistrationOrder.OrderStatus.PRE_REGISTERED,
        MeetingRegistrationOrder.OrderStatus.SUBMITTED,
    ):
        return _json_error('当前订单状态不支持添加报名人。')

    new_count = int(request.POST.get('new_attendee_count', 0))
    if new_count < 1:
        return _json_error('请至少添加一位参会人。')

    participants, participant_errors = build_participants(request.POST, request.FILES, new_count)
    if participant_errors:
        return _json_error('请补全参会人信息。', errors=participant_errors)

    existing_count = order.participants.count()
    max_group_size = max(page.max_group_size, page.min_group_size, 2)
    if existing_count + len(participants) > max_group_size:
        return _json_error(f'总参会人数不能超过 {max_group_size} 位。')

    for index, participant in enumerate(participants, start=existing_count + 1):
        MeetingParticipant.objects.create(
            order=order,
            sort_order=index,
            full_name=participant['full_name'],
            phone_number=participant['phone_number'],
            email=participant.get('email', ''),
            department=participant.get('department', ''),
            job_title=participant.get('job_title', ''),
            organization=participant.get('organization', ''),
            invoice_tax_number=participant.get('invoice_tax_number', ''),
            invoice_title_choice=participant.get('invoice_title_choice', 'same_as_org'),
            notes=participant.get('notes', ''),
            avatar_photo=participant.get('avatar_photo'),
        )

    previous_total_amount = order.total_amount
    total_count = order.participants.count()
    order.attendee_count = total_count
    order.registration_type = 'group' if total_count >= 2 else 'single'
    order.total_amount = page.ticket_price * Decimal(total_count)

    message = f'成功添加 {len(participants)} 位参会人，当前共 {total_count} 位。'
    update_fields = ['attendee_count', 'registration_type', 'total_amount', 'updated_at']
    if order.order_status == MeetingRegistrationOrder.OrderStatus.SUBMITTED:
        if order.paid_amount < previous_total_amount:
            order.paid_amount = previous_total_amount
        order.order_status = MeetingRegistrationOrder.OrderStatus.PRE_REGISTERED
        order.payment_status = MeetingRegistrationOrder.PaymentStatus.UNPAID
        order.payment_provider_trade_no = ''
        order.payment_qr_payload = ''
        order.payment_response = {}
        order.payment_checked_at = None
        order.paid_at = None
        update_fields.extend([
            'paid_amount',
            'order_status',
            'payment_status',
            'payment_provider_trade_no',
            'payment_qr_payload',
            'payment_response',
            'payment_checked_at',
            'paid_at',
        ])
        message += f' 新增人员后需重新完成补缴并提交确认，待补金额：￥{order.outstanding_amount_display}。'

    order.save(update_fields=update_fields)

    return JsonResponse({
        'ok': True,
        'message': message,
        'attendee_count': total_count,
        'total_amount': order.total_amount_display,
        'paid_amount': order.paid_amount_display,
        'outstanding_amount': order.outstanding_amount_display,
        'order_status': order.order_status,
        'payment_status': order.payment_status,
    })


@require_POST
def resume_mobile_payment(request):
    page = _get_page(request.POST.get('page_id'))
    order = _get_order(page, (request.POST.get('order_id') or '').strip())
    resume_kind = (request.POST.get('resume_kind') or 'create').strip()
    try:
        payload = _build_mobile_wechat_payment_response(request, order, resume_kind=resume_kind)
    except PaymentConfigurationError as exc:
        logger.warning(
            'WeChat mobile payment resume configuration issue: order_id=%s out_trade_no=%s reason=%s',
            order.public_id,
            order.out_trade_no,
            exc,
        )
        payload = None
    except PaymentGatewayError as exc:
        logger.warning(
            'WeChat mobile payment resume gateway issue: order_id=%s out_trade_no=%s reason=%s',
            order.public_id,
            order.out_trade_no,
            exc,
        )
        payload = None
    if not payload:
        order.payment_status = MeetingRegistrationOrder.PaymentStatus.PENDING
        order.payment_qr_payload = 'static'
        order.payment_response = {'manual': True, 'resume_kind': resume_kind}
        order.save(update_fields=['payment_status', 'payment_qr_payload', 'payment_response', 'updated_at'])
        amount = order.outstanding_amount_display if resume_kind == 'prepay' else order.total_amount_display
        return JsonResponse(_manual_qr_payload(order, amount=amount, include_totals=(resume_kind == 'prepay'), request=request))
    return JsonResponse(payload)


def wechat_oauth_callback(request):
    code = (request.GET.get('code') or '').strip()
    state = (request.GET.get('state') or '').strip()
    if not code or not state:
        return HttpResponse('微信授权参数缺失。', status=400)
    try:
        payload = _read_wechat_oauth_state(state)
        openid = _exchange_wechat_oauth_code(code)
    except Exception as exc:
        return HttpResponse(str(exc), status=400)
    request.session['wechat_openid'] = openid
    order = MeetingRegistrationOrder.objects.filter(public_id=payload.get('order_id')).select_related('page').first()
    if not order:
        return HttpResponse('订单不存在。', status=404)
    return redirect(f"{order.page.url}?wechat_resume=1&resume_order={order.public_id}&resume_kind={payload.get('resume_kind', 'create')}")


@require_POST
def apply_promo_code(request):
    page = _get_page(request.POST.get('page_id'))
    order_id = (request.POST.get('order_id') or request.POST.get('draft_order_id') or '').strip()
    promo_code = (request.POST.get('promo_code') or '').strip()
    if not order_id:
        return _json_error('缺少订单信息。')
    # Length check removed
    if not _promotion_code_exists(promo_code):
        return _json_error('优惠码无效，请核对后重试。')

    order = _get_order(page, order_id)
    if order.order_status == MeetingRegistrationOrder.OrderStatus.SUBMITTED and order.payment_status == MeetingRegistrationOrder.PaymentStatus.PAID:
        return _json_error('该订单已完成报名，无需重复使用优惠码。')
    if not order.payment_channel:
        order.payment_channel = 'wechat_pay'
        order.save(update_fields=['payment_channel', 'updated_at'])
    return _finalize_paid_order(order)


@require_POST
def pay_pre_registration(request):
    """Initiate payment for a pre-registered order."""
    page = _get_page(request.POST.get('page_id'))
    order_id = request.POST.get('order_id', '')
    order = _get_order(page, order_id)

    if order.order_status != MeetingRegistrationOrder.OrderStatus.PRE_REGISTERED:
        return _json_error('该订单不是预报名状态。')

    payment_channel = request.POST.get('payment_channel', '')
    if payment_channel not in ('alipay', 'wechat_pay'):
        return _json_error('请选择支付渠道。')

    order.payment_channel = payment_channel
    # Generate a new trade number for the payment
    from .models import generate_out_trade_no
    while True:
        candidate = generate_out_trade_no()
        if not MeetingRegistrationOrder.objects.filter(out_trade_no=candidate).exists():
            order.out_trade_no = candidate
            break
    order.save(update_fields=['payment_channel', 'out_trade_no', 'updated_at'])

    if order.payment_channel == 'wechat_pay':
        try:
            mobile_payload = _build_mobile_wechat_payment_response(request, order, resume_kind='prepay')
        except PaymentConfigurationError:
            mobile_payload = None
        except PaymentGatewayError as exc:
            logger.warning(
                'Falling back to manual QR during pay_pre_registration: order_id=%s out_trade_no=%s reason=%s',
                order.public_id,
                order.out_trade_no,
                exc,
            )
            mobile_payload = None
        if mobile_payload:
            mobile_payload.update({
                'total_amount': order.total_amount_display,
                'paid_amount': order.paid_amount_display,
                'outstanding_amount': order.outstanding_amount_display,
            })
            return JsonResponse(mobile_payload)

    order.payment_status = MeetingRegistrationOrder.PaymentStatus.PENDING
    order.payment_qr_payload = 'static'
    order.payment_response = {'manual': True}
    order.save(update_fields=['payment_status', 'payment_qr_payload', 'payment_response', 'updated_at'])

    return JsonResponse(_manual_qr_payload(order, amount=order.outstanding_amount_display, include_totals=True, request=request))


@csrf_exempt
@require_POST
def alipay_notify(request):
    out_trade_no = (request.POST.get('out_trade_no') or '').strip()
    order = MeetingRegistrationOrder.objects.filter(out_trade_no=out_trade_no).first()
    if not order:
        return HttpResponse('success')
    try:
        result = query_payment(order)
    except Exception:
        return HttpResponse('failure', status=400)
    if result.get('paid'):
        _mark_order_paid(order, trade_no=result.get('trade_no', ''), raw=result.get('raw'))
    return HttpResponse('success')


def alipay_return(request):
    out_trade_no = (request.GET.get('out_trade_no') or '').strip()
    order = MeetingRegistrationOrder.objects.filter(out_trade_no=out_trade_no).select_related('page').first()
    if not order:
        return HttpResponse('订单不存在。', status=404)
    result = query_payment(order)
    if result.get('paid'):
        _mark_order_paid(order, trade_no=result.get('trade_no', ''), raw=result.get('raw'))
        return _alipay_redirect_response(order)
    return redirect(f'{order.page.url}?payment_status=pending&order={order.public_id}')


@csrf_exempt
@require_POST
def wechat_notify(request):
    try:
        payload = _wechat_client().callback(dict(request.headers), request.body)
        resource = payload.get('resource') or {}
        out_trade_no = resource.get('out_trade_no', '')
        order = MeetingRegistrationOrder.objects.filter(out_trade_no=out_trade_no).first()
        if order and payload.get('event_type') == 'TRANSACTION.SUCCESS':
            amount_total = ((resource.get('amount') or {}).get('total') or 0)
            paid_amount = Decimal(str(amount_total)) / Decimal('100') if amount_total else None
            _mark_order_paid(
                order,
                amount=paid_amount,
                trade_no=resource.get('transaction_id', ''),
                raw=payload,
            )
        return JsonResponse({'code': 'SUCCESS', 'message': 'OK'})
    except Exception:
        return JsonResponse({'code': 'FAIL', 'message': 'FAIL'}, status=400)


import json, os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

BUFFER_FILE = '/tmp/input_buffer.json'

@csrf_exempt
def input_test(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        with open(BUFFER_FILE, 'w') as f:
            json.dump(data, f)
        return JsonResponse({'ok': True})
    
    # GET 请求返回当前内容
    content = {'text': '', 'image': ''}
    if os.path.exists(BUFFER_FILE):
        try:
            with open(BUFFER_FILE, 'r') as f:
                content = json.load(f)
        except:
            pass
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(content)
    
    return render(request, 'meetings/inputtest.html', {'content': content})


# ──────────────────────────────────────────────────────────────
# 收款 Webhook  &  收款确认管理界面
# ──────────────────────────────────────────────────────────────

from .models import PaymentWebhookEvent


def _verify_webhook_token(request):
    """校验 webhook token：支持 query param ?token= 或 Authorization: Bearer <token>"""
    expected = getattr(settings, 'PAYMENT_WEBHOOK_TOKEN', '')
    if not expected:
        return False  # 未配置 token，拒绝一切请求
    # 从 query string 取
    token = request.GET.get('token', '').strip()
    if not token:
        # 从 Authorization header 取
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            token = auth[7:].strip()
    return token == expected


@csrf_exempt
def payment_webhook(request):
    """
    收款通知 Webhook 入口。
    支持 GET（iOS 快捷指令 URL scheme 调用）和 POST（JSON body）。
    必须携带正确的 token 参数。

    示例 GET 调用（iOS 快捷指令）：
      https://ph3.711177.xyz/api/payment-webhook/?token=YOUR_TOKEN
        &amount=2500.00&payer=张三&channel=alipay
        &remark=会议报名&trade_no=2026xxxx&sms=原始短信内容

    示例 POST 调用（JSON）：
      POST https://ph3.711177.xyz/api/payment-webhook/?token=YOUR_TOKEN
      {"amount":"2500.00","payer":"张三","channel":"alipay",...}
    """
    if not _verify_webhook_token(request):
        return JsonResponse({'ok': False, 'message': '无效的 token'}, status=403)

    # 解析 payload
    if request.method == 'POST':
        try:
            body = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            # 也允许 form-encoded POST
            body = request.POST.dict()
    else:
        body = request.GET.dict()
        body.pop('token', None)

    amount = str(body.get('amount', '')).strip()
    payer = str(body.get('payer', '')).strip()
    channel = str(body.get('channel', body.get('payment_channel', ''))).strip()
    remark = str(body.get('remark', '')).strip()
    trade_no = str(body.get('trade_no', '')).strip()
    sms_body = str(body.get('sms', body.get('sms_body', ''))).strip()
    source = str(body.get('source', 'ios_shortcut')).strip()

    event = PaymentWebhookEvent.objects.create(
        source=source,
        amount=amount,
        payer=payer,
        payment_channel=channel,
        remark=remark,
        trade_no=trade_no,
        sms_body=sms_body,
        raw_payload=body,
        client_ip=_get_client_ip(request),
    )

    # 尝试自动按金额 + 备注模糊匹配订单
    if amount:
        try:
            from decimal import Decimal as D
            amt = D(amount)
            pending_orders = MeetingRegistrationOrder.objects.filter(
                total_amount=amt,
                payment_status=MeetingRegistrationOrder.PaymentStatus.PENDING,
            )
            if pending_orders.count() == 1:
                event.matched_order = pending_orders.first()
                event.save(update_fields=['matched_order'])
        except Exception:
            pass

    return JsonResponse({
        'ok': True,
        'event_id': event.pk,
        'message': f'收款通知已记录，金额 ¥{amount}，付款方 {payer}',
    })


@csrf_exempt
def payment_webhook_events_api(request):
    """返回最近 50 条收款事件（JSON），供收款确认界面轮询。"""
    if not _verify_webhook_token(request):
        return JsonResponse({'ok': False, 'message': '无效的 token'}, status=403)

    events = PaymentWebhookEvent.objects.select_related('matched_order').order_by('-received_at')[:50]
    data = []
    for e in events:
        data.append({
            'id': e.pk,
            'received_at': timezone.localtime(e.received_at).strftime('%Y-%m-%d %H:%M:%S'),
            'amount': e.amount,
            'payer': e.payer,
            'channel': e.payment_channel,
            'remark': e.remark,
            'trade_no': e.trade_no,
            'sms_body': e.sms_body,
            'source': e.source,
            'processed': e.processed,
            'matched_order_id': e.matched_order.public_id if e.matched_order else '',
            'client_ip': e.client_ip,
        })
    return JsonResponse({'ok': True, 'events': data})


def payment_dashboard(request):
    """收款确认管理界面（需要 token 访问）。"""
    if not _verify_webhook_token(request):
        return HttpResponse(
            '<h2 style="font-family:sans-serif;margin:2rem;">⛔ 需要正确的 token 参数</h2>'
            '<p style="font-family:sans-serif;margin:2rem;">请在 URL 后加 <code>?token=YOUR_TOKEN</code></p>',
            status=403,
        )
    token = request.GET.get('token', '')
    # 取最近 100 条事件用于初始渲染
    events = PaymentWebhookEvent.objects.select_related('matched_order').order_by('-received_at')[:100]
    # 取待支付订单列表，供人工匹配
    pending_orders = MeetingRegistrationOrder.objects.filter(
        payment_status=MeetingRegistrationOrder.PaymentStatus.PENDING,
    ).order_by('-created_at')[:50]
    return render(request, 'meetings/payment_dashboard.html', {
        'events': events,
        'pending_orders': pending_orders,
        'token': token,
    })


@csrf_exempt
@require_POST
def payment_event_mark(request):
    """标记事件为已处理，或手动匹配订单。"""
    if not _verify_webhook_token(request):
        return JsonResponse({'ok': False, 'message': '无效的 token'}, status=403)
    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        body = request.POST.dict()
    event_id = body.get('event_id')
    event = get_object_or_404(PaymentWebhookEvent, pk=event_id)
    if 'processed' in body:
        event.processed = bool(body['processed'])
    if 'order_id' in body:
        order_id = str(body['order_id']).strip()
        if order_id:
            order = MeetingRegistrationOrder.objects.filter(public_id=order_id).first()
            event.matched_order = order
        else:
            event.matched_order = None
    event.save()
    return JsonResponse({'ok': True, 'message': '已更新'})

@require_POST
def submit_manual_payment(request):
    """Marks an unpaid manual order as SUBMITTED and sends an admin notification."""
    page = _get_page(request.POST.get('page_id'))
    order = _get_order(page, request.POST.get('draft_order_id', ''))
    
    if order.order_status == MeetingRegistrationOrder.OrderStatus.DRAFT:
        order.order_status = MeetingRegistrationOrder.OrderStatus.SUBMITTED
        order.submitted_at = timezone.now()
        order.save(update_fields=['order_status', 'submitted_at', 'updated_at'])

    admin_email = getattr(settings, 'PAYMENT_ADMIN_EMAIL', 'events@daxa.ltd')
    token = getattr(settings, 'PAYMENT_WEBHOOK_TOKEN', 'daxa_payment_token_default_value')
    # Use request context or hardcoded host
    scheme = request.scheme
    host = request.get_host()
    confirm_url = f'{scheme}://{host}/api/manual-webhook-confirm/?order_id={order.public_id}&token={token}'
    
    body = f"""
有新的订单提交了手动支付：

订单号：{order.public_id}
预订人姓名：{order.contact_name}
联系电话：{order.contact_phone}
报名人数：{order.attendee_count}
金额：￥{order.total_amount}
支付方式：{order.get_payment_channel_display()}

确认收款后，请点击下方链接将其标记为已支付：
{confirm_url}
"""
    try:
        from django.core.mail import send_mail
        send_mail(
            f'【手动支付待确认】订单 {order.public_id}',
            body,
            settings.DEFAULT_FROM_EMAIL,
            [admin_email],
            fail_silently=True,
        )
    except Exception:
        pass
        
    response = JsonResponse({
        'ok': True,
        'redirect_url': f'{page.url}?submitted=1&order={order.public_id}',
        'message': '报名已提交，请等待确认。'
    })
    response.set_cookie('mr_order_id', order.public_id, max_age=90 * 86400, httponly=True, samesite='Lax')
    return response

def manual_webhook_confirm(request):
    """GET endpoint for email webhook to confirm payment."""
    if not _verify_webhook_token(request):
        return HttpResponse('无效的token，拒绝访问。', status=403)
        
    order_id = request.GET.get('order_id')
    if not order_id:
        return HttpResponse('缺少 order_id。', status=400)
        
    order = get_object_or_404(MeetingRegistrationOrder, public_id=order_id)
    updated = False
    update_fields = []
    
    if order.payment_status != MeetingRegistrationOrder.PaymentStatus.PAID or order.paid_amount != order.total_amount:
        order.payment_status = MeetingRegistrationOrder.PaymentStatus.PAID
        order.paid_amount = order.total_amount
        order.paid_at = timezone.now()
        update_fields.extend(['payment_status', 'paid_amount', 'paid_at', 'updated_at'])
        updated = True
        
    if order.order_status == MeetingRegistrationOrder.OrderStatus.PRE_REGISTERED:
        order.order_status = MeetingRegistrationOrder.OrderStatus.SUBMITTED
        if 'updated_at' not in update_fields:
            update_fields.append('updated_at')
        update_fields.append('order_status')
        updated = True
            
    if updated:
        order.save(update_fields=update_fields)
        
        # Send confirmation to user
        try:
            send_registration_email(order, 'paid')
        except Exception:
            pass
            
    return HttpResponse(f'<h3>支付确认成功！</h3><p>订单 {order.public_id} 已标记为已支付，并向用户发送了确认邮件。</p>')
