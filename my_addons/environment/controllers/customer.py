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
  
    @http.route('/order', type='http', auth='public', methods=['POST'], csrf=False)
    def order_create(self, **kw):
        """
        API tạo thanh toán cho hợp đồng qua VNPAY
        Body JSON: { "contract_id": 1, "months_paid": 3 }
        """
        try:
            data = request.get_json_data()
            _logger.info("=== Nhận JSON body: %s", data)

            contract_id = int(data.get("contract_id", 0))
            months_paid = int(data.get("months_paid", 0))

            if not contract_id or months_paid <= 0:
                return request.make_json_response(
                    {"error": "contract_id và months_paid là bắt buộc và > 0"}, status=400
                )

            # lấy contract
            contract = request.env["env.contract"].sudo().browse(contract_id)
            if not contract.exists():
                return request.make_json_response({"error": "Hợp đồng không tồn tại"}, status=404)

            # check tổng số tháng đã thanh toán
            already_paid = sum(contract.orders.mapped("months_paid"))
            try:
                contract_term = int(contract.contract_term or 0)
            except ValueError:
                contract_term = 0

            if already_paid + months_paid > contract_term:
                return request.make_json_response(
                    {
                        "error": f"Tổng số tháng thanh toán ({already_paid + months_paid}) vượt quá thời hạn hợp đồng {contract_term} tháng."
                    },
                    status=400,
                )

            # tính tổng tiền
            total_amount = months_paid * contract.monthly_amount
            _logger.info("=== Tổng tiền: %s, hợp đồng: %s", total_amount, contract.id)

            # build url thanh toán
            current_domain = request.httprequest.host_url.rstrip("/")
            VNPAY_RETURN_URL = f"{current_domain}/orders/payment_return?contract_id={contract.id}&months_paid={months_paid}"            
            vnp = vnpay()
            txn_ref = f"{contract.id}_{int(datetime.now().timestamp())}"
            vnp.requestData = {
                "vnp_Version": "2.1.0",
                "vnp_Command": "pay",
                "vnp_TmnCode": VNPAY_TMNCODE,
                "vnp_Amount": str(int(total_amount) * 100),  # VND * 100
                "vnp_CurrCode": "VND",
                "vnp_TxnRef": txn_ref,  # dùng contract.id làm mã tham chiếu
                "vnp_OrderInfo": f"Thanh toan hop dong {contract.id} - {months_paid} thang",
                "vnp_OrderType": "other",
                "vnp_Locale": "vn",
                "vnp_CreateDate": datetime.now().strftime("%Y%m%d%H%M%S"),
                "vnp_IpAddr": request.httprequest.remote_addr,
                "vnp_ReturnUrl": VNPAY_RETURN_URL,
            }
            _logger.info("=== Request data gửi sang VNPAY: %s", vnp.requestData)
            payment_url = vnp.get_payment_url(VNPAY_URL, VNPAY_HASH_SECRET)
            _logger.info("=== payment_url: %s", payment_url)

            # trả JSON về cho FE
            return request.make_json_response({"payment_url": payment_url})

        except Exception as e:
            _logger.error("=== Lỗi: %s", str(e))
            return request.make_json_response({"error": str(e)}, status=500)

    @http.route('/orders/payment_return', type='http', auth='public', methods=['GET'], csrf=False)
    def payment_return(self, **kwargs):
        query_params = kwargs  # VNPAY trả về qua query string

        contract_id = query_params.get("contract_id")
        months_paid = query_params.get("months_paid")
        txn_ref = query_params.get("vnp_TxnRef")
        response_code = query_params.get("vnp_ResponseCode")  # mã phản hồi của VNPAY

        if not contract_id or not months_paid:
            return request.redirect("/payment_result?status=fail&reason=missing_params")

        contract = request.env["env.contract"].sudo().browse(int(contract_id))
        if not contract.exists():
            return request.redirect("/payment_result?status=fail&reason=contract_not_found")

        # Thanh toán thành công
        if response_code == "00":
            order = request.env["env.contract.order"].sudo().create({
                "contract_id": contract.id,
                "months_paid": int(months_paid),
            })
            status = "success"
            order_id = order.id
        else:
            status = "fail"
            order_id = ""

        # Redirect về FE
        redirect_url = f"http://localhost:8069/payment_result?contract_id={contract.id}&order_id={order_id}&status={status}"
        return request.redirect(redirect_url)

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

    @http.route('/home', auth='public', website=True)
    def home(self, **kw):
        return request.render('environment.home_template')
    
    @http.route('/customers', auth='public', website=True)
    def customers(self, **kw):
        domain = []
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

