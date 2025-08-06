from odoo import models, fields

class ServicePriceComponent(models.Model):
    _name = 'env.servicepricecomponent'
    _description = 'Service Price Component'
    _inherit = 'env.base'  # nếu bạn đã có BaseModel

    name = fields.Char(string="Mã thành phần", required=True)
    
    service_price_id = fields.Many2one(
        comodel_name='env.serviceprice',
        string='Bảng giá dịch vụ',
        required=True,
        ondelete='cascade'
    )

    component_name = fields.Char(string="Tên thành phần giá", required=True)
    amount = fields.Float(string="Giá trị", required=True)
    unit = fields.Selection(
        selection=[
            ('kg', 'Kg'),
            ('month', 'Month')
        ],
        string="Đơn vị tính",
        required=True
    )
    description = fields.Text(string="Mô tả thêm")