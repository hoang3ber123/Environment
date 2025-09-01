from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import AccessError


class CollectionUnitGroup(models.Model):
    _name = 'env.collectionunitgroup'
    _description = 'Nhóm nhân viên trong đơn vị thu gom'
    _inherit = 'env.base'

    name = fields.Char(string="Tên nhóm", required=True)
    collection_unit_id = fields.Many2one(
        'env.collectionunit',
        string="Đơn vị thu gom",
        required=True,
        ondelete="cascade"
    )
    member_ids = fields.Many2many(
        'res.users',
        'collectionunit_group_user_rel',
        'group_id', 'user_id',
        string="Nhân viên"
    )
    action_ids = fields.Many2many(
        'env.collectionunitaction',
        'collectionunit_group_action_rel',
        'group_id', 'action_id',
        string="Quyền hạn"
    )

class CollectionUnitAction(models.Model):
    _name = 'env.collectionunitaction'
    _description = 'Quyền hành động của nhóm'
    _inherit = 'env.base'

    name = fields.Char(string="Tên hành động", required=True, readonly=True)
    code = fields.Char(
        string="Mã quyền",
        required=True,
        readonly=True,
        index=True
    )

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mã quyền phải duy nhất.')
    ]

    @api.model
    def create(self, vals):
        # Cho phép khi đang cài module (user = SUPERUSER_ID và context có module install)
        if self.env.uid == SUPERUSER_ID and self.env.context.get('install_mode'):
            return super().create(vals)
        raise AccessError("Không được phép tạo mới quyền hành động. Quyền này là cố định.")

    def write(self, vals):
        if self.env.uid == SUPERUSER_ID and self.env.context.get('install_mode'):
            return super().write(vals)
        raise AccessError("Không được phép sửa quyền hành động. Quyền này là cố định.")