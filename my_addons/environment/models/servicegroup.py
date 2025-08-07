from odoo import models, fields, api
class ServiceGroup(models.Model):
    _name = 'env.servicegroup'
    _description = 'Nhóm dịch vụ'
    _inherit = 'env.base'

    name = fields.Char(
        required=True,
        string="Tên nhóm dịch vụ",
        help="Tên của nhóm dịch vụ (VD: Nhóm thu gom, Nhóm xử lý...)"
    )

    code = fields.Char(
        required=True,
        string="Mã nhóm",
        copy=False,
        help="Mã viết tắt của nhóm dịch vụ, tự sinh từ tên nếu không nhập."
    )

    description = fields.Char(
        string="Mô tả",
        help="Ghi chú hoặc mô tả thêm cho nhóm dịch vụ (nếu có)."
    )

    status = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('active', 'Đang hoạt động'),
            ('stopping', 'Ngừng hoạt động'),
        ],
        string="Trạng thái",
        default='draft',
        required=True,
        help="Trạng thái hiện tại của nhóm dịch vụ."
    )

    service_ids = fields.One2many(
        'env.service',
        'groupservice_id',
        string='Danh sách dịch vụ',
        help="Các dịch vụ thuộc nhóm này."
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã nhóm (Code) phải là duy nhất.'),
        ('name_uniq', 'unique(name)', 'Tên nhóm (Name) phải là duy nhất.'),
    ]

    @api.model
    def create(self, vals):
        # Tự sinh code từ tên nếu không có hoặc rỗng
        if not vals.get('code'):
            name = vals.get('name', '')
            code = ''.join([word[0].upper() for word in name.split() if word])[:5]
            vals['code'] = code
        return super().create(vals)

    def write(self, vals):
        # Nếu đổi name mà không truyền code thì cập nhật lại code tương tự
        for rec in self:
            if 'name' in vals and not vals.get('code'):
                name = vals.get('name') or rec.name or ''
                new_code = ''.join([word[0].upper() for word in name.split() if word])[:5]
                vals['code'] = new_code
        return super().write(vals)