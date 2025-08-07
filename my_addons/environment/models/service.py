from odoo import models, fields, api
class Service(models.Model):
    _name = 'env.service'
    _description = 'Service'
    _inherit = 'env.base'

    name = fields.Char(
        required=True,
        string="Tên dịch vụ",
        help="Tên hiển thị của dịch vụ, dùng để phân biệt giữa các loại dịch vụ khác nhau."
    )
    code = fields.Char(
        required=True,
        string="Mã dịch vụ",
        copy=False,
        index=True,
        unique=True,
        help="Mã dịch vụ là duy nhất. Nếu không nhập, hệ thống sẽ tự sinh dựa trên tên."
    )
    description = fields.Text(
        string="Mô tả",
        help="Mô tả chi tiết về dịch vụ, có thể bao gồm thông tin kỹ thuật hoặc lưu ý sử dụng."
    )
    scope = fields.Char(
        string="Phạm vi áp dụng",
        help="Phạm vi mà dịch vụ này được áp dụng, ví dụ: toàn phường, toàn xã, hoặc khu vực cụ thể."
    )
    status = fields.Selection(
        selection=[
            ('draft', 'Nháp'),
            ('active', 'Hoạt động'),
            ('stopping', 'Ngưng sử dụng')
        ],
        string="Trạng thái",
        default='draft',
        help="Trạng thái hiện tại của dịch vụ."
    )
    groupservice_id = fields.Many2one(
        'env.servicegroup',
        string='Nhóm dịch vụ',
        help="Nhóm mà dịch vụ này thuộc về, giúp phân loại và tổ chức dịch vụ."
    )

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Mã dịch vụ phải là duy nhất.')
    ]

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            name = vals.get('name', '')
            code = ''.join([word[0].upper() for word in name.split() if word])[:5]
            vals['code'] = code
        return super().create(vals)

    def write(self, vals):
        if 'name' in vals and 'code' not in vals:
            name = vals['name']
            code = ''.join([word[0].upper() for word in name.split() if word])[:5]
            vals['code'] = code
        return super().write(vals)