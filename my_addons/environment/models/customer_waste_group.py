from odoo import models, fields, api
class CustomerWasteGroup(models.Model):
    _name = 'env.customerwastegroup'
    _description = 'Customer Waste Group'
    _inherit = 'env.base'

    name = fields.Char(required=True, string="Name", help="Tên nhóm khách hàng (VD: Hộ gia đình, Nhóm 1...)")
    code = fields.Char(required=True, string="Code", help="Mã viết tắt của nhóm (VD: HGD, N1...)", copy=False)
    customer_type = fields.Char(string="Customer Type", help="Loại khách hàng thuộc nhóm (VD: hộ gia đình, cơ sở kinh doanh...)")
    waste_volume_min = fields.Float(required=True, string="Waste Volume Min (kg)", help="Lượng rác tối thiểu (kg) để thuộc nhóm")
    waste_volume_max = fields.Float(string="Waste Volume Max (kg)", help="Lượng rác tối đa (kg). Nếu không có nghĩa là không giới hạn trên")
    pricing_method = fields.Selection(
        selection=[
            ('fixed_monthly', 'Fixed monthly'),
            ('per_kg', 'Per kg'),
        ],
        required=True,
        string="Pricing Method",
        help="Phương thức tính phí"
    )
    description = fields.Text(string="Description", help="Ghi chú/mô tả thêm (nếu có)")
    status = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('stopping', 'Stopping'),
        ],
        string="Status",
        required=True,
        default='draft',
        help="Trạng thái nhóm dịch vụ"
    )
    service_ids = fields.One2many('env.service', 'groupservice_id', string='Services')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code phải là duy nhất.'),
        ('name_uniq', 'unique(name)', 'Name phải là duy nhất.'),
    ]

    @api.constrains('waste_volume_min', 'waste_volume_max')
    def _check_volume_bounds(self):
        for rec in self:
            if rec.waste_volume_max and rec.waste_volume_min > rec.waste_volume_max:
                raise ValidationError(_("`Waste Volume Min` không được lớn hơn `Waste Volume Max`."))

    @api.model
    def create(self, vals):
        # Tự sinh code từ tên nếu không có hoặc rỗng
        if not vals.get('code'):
            name = vals.get('name', '')
            code = ''.join([word[0].upper() for word in name.split() if word])[:5]
            vals['code'] = code
        return super().create(vals)

    def write(self, vals):
        # Nếu đổi name mà không truyền code thì cập nhật lại code tương tự (không ghi đè nếu user explicitly truyền code="")
        for rec in self:
            if 'name' in vals and not vals.get('code'):
                name = vals.get('name') or rec.name or ''
                new_code = ''.join([word[0].upper() for word in name.split() if word])[:5]
                vals['code'] = new_code
        return super().write(vals)