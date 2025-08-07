from odoo import models, fields, api

class Location(models.Model):
    _name = 'env.location'
    _description = 'Địa giới hành chính'
    _inherit = 'env.base'

    name = fields.Char(
        required=True,
        string="Tên địa phương",
        readonly=True,
        help="Tên địa phương (VD: Phường 1, Quận 5, TP. Hồ Chí Minh). Được nhập từ dữ liệu chuẩn, không cho sửa."
    )

    type = fields.Selection(
        selection=[
            ('province', 'Tỉnh / Thành phố'),
            ('district', 'Quận / Huyện'),
            ('ward', 'Phường / Xã'),
        ],
        string="Cấp hành chính",
        default='province',
        required=True,
        help="Chọn cấp hành chính tương ứng (Tỉnh, Huyện, Xã)."
    )

    code = fields.Char(
        required=True,
        string="Mã địa phương",
        readonly=True,
        help="Mã định danh của địa phương theo hệ thống. Được nhập từ dữ liệu chuẩn, không cho sửa."
    )

    full_path = fields.Char(
        required=True,
        string="Đường dẫn đầy đủ",
        readonly=True,
        help="Tên đầy đủ của địa phương theo thứ tự hành chính (VD: TP. Hồ Chí Minh > Quận 5 > Phường 1)."
    )

    parent_id = fields.Many2one(
        'env.location',
        string='Địa phương cấp trên',
        readonly=True,
        help="Địa phương cha trong cấu trúc hành chính (VD: Quận trực thuộc Thành phố, Phường trực thuộc Quận...)."
    )

    # Hiển thị tên bằng full_path
    name_get = lambda self: [(rec.id, rec.full_path) for rec in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|', ('full_path', operator, name), ('name', operator, name)] + args
        return self.search(args, limit=limit).name_get()