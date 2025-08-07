from odoo import models, fields

class ServicePriceComponent(models.Model):
    _name = 'env.servicepricecomponent'
    _description = 'Service Price Component'
    _inherit = 'env.base'

    name = fields.Char(
        string="Mã thành phần",
        required=True,
        help="Mã định danh nội bộ cho thành phần giá (có thể là ký hiệu viết tắt)."
    )

    service_price_id = fields.Many2one(
        comodel_name='env.serviceprice',
        string='Bảng giá dịch vụ',
        required=True,
        ondelete='cascade',
        help="Liên kết đến bảng giá dịch vụ chứa thành phần này."
    )

    component_name = fields.Char(
        string="Tên thành phần giá",
        required=True,
        help="Tên mô tả chi tiết của thành phần giá (ví dụ: Phí thu gom, Phí xử lý...)."
    )

    amount = fields.Float(
        string="Giá trị",
        required=True,
        help="Giá trị của thành phần (ví dụ: 5.000 đồng/kg hoặc 10.000 đồng/tháng)."
    )

    unit = fields.Selection(
        selection=[
            ('kg', 'Kg'),
            ('month', 'Tháng'),
        ],
        string="Đơn vị tính",
        required=True,
        help="Đơn vị tính cho thành phần giá."
    )

    description = fields.Text(
        string="Mô tả thêm",
        help="Ghi chú bổ sung về thành phần giá nếu có."
    )