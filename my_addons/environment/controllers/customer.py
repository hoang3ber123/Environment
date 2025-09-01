import logging
_logger = logging.getLogger(__name__)
from odoo import http
from odoo.http import request
from ..utils.vnpay import vnpay
from datetime import datetime
VNPAY_URL = "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html"
VNPAY_TMNCODE = "LZPLRB1E"
VNPAY_HASH_SECRET = "APBHTE4INVHF4PE8N0DBU6G09NHAMWQU"
VNPAY_RETURN_URL = "http://localhost:8080/vnpay/payment_return"
class CustomerController(http.Controller):
    @http.route('/order/test_fixed', type='http', auth='public', methods=['GET'], csrf=False)
    def test_fixed_payment(self, **kw):
        """
        API test thanh toán VNPAY với dữ liệu cứng:
        - contract_id = 1
        - tổng tiền = 100.000 VND
        """
        try:
            contract_id = 1
            total_amount = 100000  # 100k VND
            txn_ref = f"TEST_{int(datetime.now().timestamp())}"

            # build url callback
            current_domain = request.httprequest.host_url.rstrip("/")
            return_url = f"{current_domain}/orders/payment_return?status=success&contract_id={contract_id}"

            # tạo object VNPAY
            vnp = vnpay()
            # tất cả giá trị phải là chuỗi, không để int hay None
            vnp.requestData = {
                "vnp_Version": "2.1.0",
                "vnp_Command": "pay",
                "vnp_TmnCode": str(VNPAY_TMNCODE),
                "vnp_Amount": str(int(total_amount) * 100),
                "vnp_CurrCode": "VND",
                "vnp_TxnRef": str(txn_ref),
                "vnp_OrderInfo": f"thanh toan hop dong {contract_id}",
                "vnp_OrderType": "other",
                "vnp_Locale": "vn",
                "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
                "vnp_ReturnUrl": return_url,
                "vnp_IpAddr": request.httprequest.remote_addr or "127.0.0.1",
            }

            # gọi hàm bạn có sẵn để lấy URL
            payment_url = vnp.get_payment_url(VNPAY_URL, VNPAY_HASH_SECRET)
            _logger.info(f"=== Payment URL test: {payment_url}")

            # trả về JSON chuẩn API
            return request.redirect(payment_url)

        except Exception as e:
            _logger.error(f"=== Lỗi khi tạo payment test: {e}", exc_info=True)
            return request.make_json_response({"error": str(e)}, status=500)
    
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
            month_ids_str = ",".join(str(m.id) for m in months)
            VNPAY_RETURN_URL = f"{current_domain}/orders/payment_return?contract_id={contract.id}&month_ids={month_ids_str}"

            vnp = vnpay()
            txn_ref = f"{contract.id}_{int(datetime.now().timestamp())}"
            vnp.requestData = {
                "vnp_Version": "2.1.0",
                "vnp_Command": "pay",
                "vnp_TmnCode": VNPAY_TMNCODE,
                "vnp_Amount": str(int(total_amount) * 100),  # VND * 100
                "vnp_CurrCode": "VND",
                "vnp_TxnRef": txn_ref,
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
        contract_id = kwargs.get("contract_id")
        month_ids_str = kwargs.get("month_ids")
        response_code = kwargs.get("vnp_ResponseCode")

        if not contract_id or not month_ids_str:
            return request.redirect("/payment_result?status=fail&reason=missing_params")

        contract = request.env["env.contract"].sudo().browse(int(contract_id))
        if not contract.exists():
            return request.redirect("/payment_result?status=fail&reason=contract_not_found")

        month_ids = [int(x) for x in month_ids_str.split(",") if x]
        months = request.env["env.contract.month"].sudo().browse(month_ids)

        if response_code == "00":
            # Tính total_amount ngay tại đây
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

