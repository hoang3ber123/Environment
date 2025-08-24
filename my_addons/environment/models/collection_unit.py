from odoo import models, fields, api
from odoo.exceptions import ValidationError
class CollectionUnit(models.Model):
    _name = 'env.collectionunit'
    _description = 'Đơn vị thu gom'
    _inherit = 'env.base'

    name = fields.Char(
        required=True,
        string="Tên đơn vị thu gom",
        help="Nhập tên đầy đủ của đơn vị thu gom (VD: Công ty Môi Trường Xanh, Tổ thu gom số 5...)."
    )

    code = fields.Char(
        string="Mã đơn vị",
        help="Mã định danh duy nhất của đơn vị thu gom (nếu có)."
    )

    phone = fields.Char(
        string="Số điện thoại liên hệ",
        help="Số điện thoại của đơn vị thu gom."
    )

    email = fields.Char(
        string="Email liên hệ",
        help="Email chính thức của đơn vị thu gom."
    )

    location_ids = fields.Many2many(
        comodel_name='env.location',
        relation='collection_unit_location_rel',
        column1='collection_unit_id',
        column2='location_id',
        string="Khu vực phụ trách",
        help="Danh sách các địa phương mà đơn vị này phụ trách thu gom."
    )

    manager_id = fields.Many2one(
        comodel_name='res.users',
        string="Người quản lý",
        help="Người chịu trách nhiệm quản lý đơn vị thu gom."
    )

    description = fields.Text(
        string="Mô tả",
        help="Ghi chú thêm về đơn vị thu gom hoặc phạm vi hoạt động."
    )

    status = fields.Selection(
        selection=[
            ('draft', 'Đợi hoạt động'),
            ('active', 'Đang hoạt động'),
            ('stopping', 'Ngừng hoạt động'),
        ],
        string="Trạng thái",
        required=True,
        default='draft',
        help="Trạng thái của đơn vị thu gom."
    )

    service_rel_ids = fields.One2many(
        'env.unitservice',
        'collection_unit_id',
        string='Services'
    )
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Tên đơn vị thu gom phải là duy nhất.'),
        ('code_uniq', 'unique(code)', 'Mã đơn vị thu gom phải là duy nhất.')
    ]

    def _generate_unique_code(self, base_code):
        """Sinh code duy nhất dựa trên base_code, thêm số tăng dần nếu trùng"""
        code = base_code
        i = 1
        while self.search_count([('code', '=', code)]) > 0:
            code = f"{base_code}{i}"
            i += 1
        return code

    @api.model
    def create(self, vals):
        if not vals.get('code'):
            name = vals.get('name', '')
            base_code = ''.join([word[0].upper() for word in name.split() if word])[:5]
            vals['code'] = self._generate_unique_code(base_code)
        else:
            vals['code'] = self._generate_unique_code(vals['code'].upper())
        return super().create(vals)

    def write(self, vals):
        if 'name' in vals and 'code' not in vals:
            name = vals['name']
            base_code = ''.join([word[0].upper() for word in name.split() if word])[:5]
            vals['code'] = self._generate_unique_code(base_code)
        elif 'code' in vals:
            vals['code'] = self._generate_unique_code(vals['code'].upper())
        return super().write(vals)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            # Tìm theo tên đơn vị thu gom
            domain = ['|',
                ('name', operator, name),
                ('location_ids.full_path', operator, name),  # Tìm theo location full_path
            ]
        units = self.search(domain + args, limit=limit)
        return [(u.id, u.name) for u in units]

    @api.constrains('location_ids')
    def _check_existing_customers_still_valid(self):
        for unit in self:
            managed_paths = unit.location_ids.mapped('full_path')
            invalid_customers = self.env['env.customer'].search([
                ('collection_unit_id', '=', unit.id)
            ]).filtered(
                lambda c: not any(c.location_id.full_path.startswith(mp) for mp in managed_paths)
            )
            if invalid_customers:
                raise ValidationError(
                    "Không thể cập nhật phạm vi của '%s' vì có khách hàng nằm ngoài khu vực mới: %s"
                    % (unit.name, ", ".join(invalid_customers.mapped('name')))
                )