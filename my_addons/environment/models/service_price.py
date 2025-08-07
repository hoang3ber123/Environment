from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ServicePrice(models.Model):
    _name = 'env.serviceprice'
    _description = 'Service Price'
    _inherit = 'env.base'

    name = fields.Char(
        required=True,
        string="Tên bảng giá",
        help="Tên bảng giá dịch vụ (VD: Bảng giá Hộ gia đình, Nhóm 1...)"
    )
    code = fields.Char(
        required=True,
        string="Mã bảng giá",
        copy=False,
        index=True,
        help="Mã tự sinh từ tên bảng giá, là duy nhất trong hệ thống."
    )

    service_id = fields.Many2one(
        'env.service',
        string="Dịch vụ",
        required=True,
        help="Dịch vụ mà bảng giá này áp dụng."
    )

    customerwastegroup_id = fields.Many2one(
        'env.customerwastegroup',
        string="Nhóm khách hàng",
        required=True,
        help="Nhóm khách hàng mà bảng giá này áp dụng."
    )

    effective_from = fields.Date(
        required=True,
        string="Hiệu lực từ ngày",
        help="Ngày bắt đầu áp dụng bảng giá."
    )
    effective_to = fields.Date(
        string="Hiệu lực đến ngày",
        help="Ngày kết thúc áp dụng bảng giá (có thể để trống nếu không giới hạn)."
    )

    status = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('active', 'Đang áp dụng'),
            ('stopping', 'Ngừng áp dụng'),
        ],
        string="Trạng thái",
        required=True,
        default='draft',
        help="Trạng thái của bảng giá."
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã bảng giá phải là duy nhất.')
    ]

    @api.constrains('effective_from', 'effective_to')
    def _check_effective_dates(self):
        for rec in self:
            if rec.effective_to and rec.effective_from > rec.effective_to:
                raise ValidationError(_("Ngày bắt đầu không được sau ngày kết thúc."))

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            name = vals.get('name', '')
            code = ''.join([w[0].upper() for w in name.split() if w])[:5]
            vals['code'] = code
        return super().create(vals)

    def write(self, vals):
        for rec in self:
            if 'name' in vals and not vals.get('code'):
                name = vals.get('name') or rec.name or ''
                code = ''.join([w[0].upper() for w in name.split() if w])[:5]
                vals['code'] = code
        return super().write(vals)