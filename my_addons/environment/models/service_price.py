from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ServicePrice(models.Model):
    _name = 'env.serviceprice'
    _description = 'Service Price'
    _inherit = 'env.base'

    name = fields.Char(required=True, string="Name", help="Tên bảng giá dịch vụ (VD: Bảng giá Hộ gia đình, Nhóm 1...)")
    code = fields.Char(required=True, string="Code", copy=False, help="Mã tự sinh từ tên bảng giá")
    
    service_id = fields.Many2one(
        'env.service',
        string="Service",
        required=True,
        help="Dịch vụ áp dụng"
    )
    
    customerwastegroup_id = fields.Many2one(
        'env.customerwastegroup',
        string="Customer Waste Group",
        required=True,
        help="Nhóm khách hàng áp dụng"
    )

    effective_from = fields.Date(required=True, string="Effective From", help="Ngày bắt đầu áp dụng")
    effective_to = fields.Date(string="Effective To", help="Ngày kết thúc hiệu lực (có thể để trống nếu không giới hạn)")
    
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('stopping', 'Stopping'),
        ],
        string="Status",
        required=True,
        default='draft',
        help="Trạng thái bảng giá"
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code phải là duy nhất.'),
        ('name_uniq', 'unique(name)', 'Name phải là duy nhất.')
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