import logging
_logger = logging.getLogger(__name__)
from odoo import http
from odoo.http import request
from ..utils.vnpay import vnpay
from datetime import datetime
VNPAY_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNPAY_TMNCODE = "LZPLRB1E"
VNPAY_HASH_SECRET = "APBHTE4INVHF4PE8N0DBU6G09NHAMWQU"
SECRET_KEY = b"your_secret_key"
import hmac
import hashlib
import base64
import json
import time

def encode_payment_data(contract_id: int, month_ids: list[int]) -> str:
    """
    Tạo token thanh toán từ contract_id + month_ids, kèm expiry 10 phút.
    """
    data = {
        "cid": contract_id,
        "mids": month_ids,
        "exp": int(time.time()) + 600,  # hết hạn sau 10 phút
    }
    # Chuyển sang json bytes
    payload = json.dumps(data, separators=(",", ":")).encode()
    # Tạo chữ ký HMAC
    signature = hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()
    # Ghép payload + signature, encode base64 để bỏ vào URL
    token = base64.urlsafe_b64encode(payload + b"." + signature).decode()
    return token

def decode_payment_data(token: str):
    """
    Giải mã token thanh toán.
    Trả về (cid, mids) hoặc (None, None) nếu không hợp lệ/hết hạn.
    """
    try:
        raw = base64.urlsafe_b64decode(token.encode())
        payload_bytes, signature = raw.rsplit(b".", 1)
        # Kiểm tra chữ ký
        expected_sig = hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_sig):
            return None, None

        data = json.loads(payload_bytes.decode())
        if data.get("exp", 0) < time.time():
            return None, None  # token hết hạn
        return data.get("cid"), data.get("mids")
    except Exception:
        return None, None
    
class CustomerController(http.Controller): 
    @http.route('/order', type='http', auth='public', methods=['POST'], csrf=False)
    def order_create(self, **kw):
        """
        API tạo thanh toán cho hợp đồng qua VNPAY
        Body JSON: { "contract_id": 1, "month_ids": [3,4,5] }
        """
        try:
            data = request.get_json_data()
            _logger.info("=== Nhận JSON body: %s", data)

            contract_id = int(data.get("contract_id", 0))
            month_ids = data.get("months_selected", [])
            month_ids = [int(m) for m in month_ids]

            if not contract_id or not month_ids:
                return request.make_json_response(
                    {"error": "contract_id và months_selected là bắt buộc"}, status=400
                )

            # lấy contract
            contract = request.env["env.contract"].sudo().browse(contract_id)
            if not contract.exists():
                return request.make_json_response({"error": "Hợp đồng không tồn tại"}, status=404)

            # kiểm tra các tháng
            months = request.env["env.contract.month"].sudo().browse(month_ids)
            if not all(m.contract_id.id == contract.id for m in months):
                return request.make_json_response({"error": "Một số tháng không thuộc hợp đồng này"}, status=400)
            if any(m.paid for m in months):
                return request.make_json_response({"error": "Một số tháng đã thanh toán"}, status=400)

            # Tính total amount
            total_amount = len(months) * (contract.monthly_amount or 0.0)
            if total_amount <= 0:
                return request.make_json_response({"error": "Tổng tiền thanh toán không hợp lệ"}, status=400)

            # tính tổng tiền
            _logger.info("=== Tổng tiền: %s, hợp đồng: %s", total_amount, contract.id)

            # build url thanh toán
            current_domain = request.httprequest.host_url.rstrip("/")
            token = encode_payment_data(contract.id, month_ids)
            VNPAY_RETURN_URL = f"{current_domain}/orders/payment_return"

            vnp = vnpay()
            vnp.requestData = {
                "vnp_Version": "2.1.0",
                "vnp_Command": "pay",
                "vnp_TmnCode": VNPAY_TMNCODE,
                "vnp_Amount": str(int(total_amount) * 100),  # VND * 100
                "vnp_CurrCode": "VND",
                "vnp_TxnRef": token,
                "vnp_OrderInfo": f"Thanh toan hop dong {contract.id} - {len(months)} thang",
                "vnp_OrderType": "other",
                "vnp_Locale": "vn",
                "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
                "vnp_IpAddr": request.httprequest.remote_addr,
                "vnp_ReturnUrl": VNPAY_RETURN_URL,
            }
            _logger.info("=== Request data gửi sang VNPAY: %s", vnp.requestData)
            payment_url = vnp.get_payment_url(VNPAY_URL, VNPAY_HASH_SECRET)
            _logger.info("=== payment_url: %s", payment_url)

            return request.make_json_response({"payment_url": payment_url})
        except Exception as e:
            _logger.error("=== Lỗi: %s", str(e))
            return request.make_json_response({"error": str(e)}, status=500)
    
    @http.route('/orders/payment_return', type='http', auth='public', methods=['GET'], csrf=False)
    def payment_return(self, **kwargs):
        token = kwargs.get("vnp_TxnRef")  # lấy token trả về từ VNPAY
        response_code = kwargs.get("vnp_ResponseCode")

        if not token:
            return request.redirect("/payment_result?status=fail&reason=missing_token")

        # giải token
        contract_id, month_ids = decode_payment_data(token)
        if not contract_id or not month_ids:
            return request.redirect("/payment_result?status=fail&reason=invalid_or_expired_token")

        contract = request.env["env.contract"].sudo().browse(int(contract_id))
        if not contract.exists():
            return request.redirect("/payment_result?status=fail&reason=contract_not_found")

        months = request.env["env.contract.month"].sudo().browse(month_ids)

        if response_code == "00":
            # Tính total_amount
            total_amount = len(months) * (contract.monthly_amount or 0.0)

            # Tạo order
            order_vals = {
                "contract_id": contract.id,
                "months_selected": [(6, 0, month_ids)],
                "total_amount": total_amount,
            }
            order = request.env["env.contract.order"].sudo().create(order_vals)

            # Đánh dấu các tháng đã thanh toán
            for month in months:
                month.paid = True
                month.order_id = order.id

            status = "success"
            order_id = order.id
        else:
            status = "fail"
            order_id = ""

        redirect_url = f"{request.httprequest.host_url.rstrip('/')}/payment_result?contract_id={contract.id}&order_id={order_id}&status={status}"
        return request.redirect(redirect_url)

    @http.route('/contract/<int:contract_id>/months', type='http', auth='public', methods=['GET'], csrf=False)
    def get_months(self, contract_id):
        contract = request.env['env.contract'].sudo().browse(contract_id)
        if not contract:
            return {"months": []}
        months = [{
            "id": m.id,
            "name": m.name,
            "paid": m.paid
        } for m in contract.months]
        return request.make_json_response({"months": months})

    @http.route('/payment_result', type='http', auth='public', website=True)
    def payment_result(self, **kwargs):
        contract_id = kwargs.get("contract_id")
        order_id = kwargs.get("order_id")
        status = kwargs.get("status")

        return request.render("environment.payment_result_template", {
            "contract_id": contract_id,
            "order_id": order_id,
            "status": status,
        })

    @http.route('/', auth='public', website=True)
    def home(self, **kw):
        return request.render('environment.home_template')
    
    @http.route('/customers', auth='public', website=True)
    def customers(self, **kw):
        phone = kw.get("phone")
        email = kw.get("email")
        cccd = kw.get("cccd")

        # Lọc theo OR
        search_domain = []
        if phone:
            search_domain.append(('phone', '=', phone))
        if email:
            search_domain.append(('email', '=', email))
        if cccd:
            search_domain.append(('cccd', '=', cccd))

        customers = []
        if search_domain:
            customers = request.env['env.customer'].sudo().search(['|'] * (len(search_domain) - 1) + search_domain)

        values = {
            'customers': customers,
        }
        return request.render('environment.home_template', values)
    
    @http.route('/contracts/<int:customer_id>', auth='public', website=True)
    def contracts(self, customer_id, **kw):
        """Trang hiển thị danh sách hợp đồng của 1 customer"""
        contracts = request.env['env.contract'].sudo().search([
            ('customer_id', '=', customer_id)
        ])

        values = {
            'contracts': contracts,
        }
        return request.render('environment.contracts_template', values)

