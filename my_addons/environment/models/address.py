from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Address(models.Model):
    _name = 'env.address'
    _description = 'Address'
    _inherit = 'env.base'

    type = fields.Selection(
        selection=[
            ('HOUSE_SINGLE', 'Nhà ở riêng lẻ'),
            ('HOUSE_MULTI', 'Nhà nhiều hộ'),
            ('APARTMENT', 'Chung cư'),
            ('DORMITORY', 'Ký túc xá'),
            ('VILLA', 'Biệt thự'),
            ('SHOPHOUSE', 'Nhà ở kiêm kinh doanh'),
            ('BOARDING', 'Nhà trọ'),
            ('MOBILE', 'Nhà tạm/di động'),
            ('PUBLIC', 'Nhà công vụ'),
            ('SCHOOL', 'Trường học'),
        ],
        string="Type",
        required=True
    )

    street = fields.Char(required=True, string="Street")
    house_number = fields.Char(required=True, string="House Number")
    description = fields.Text(string="Description")

    full_path = fields.Char(string="Full Path", readonly=True)

    location_id = fields.Many2one(
        comodel_name='env.location',
        string="Location (Ward only)",
        domain="[('type', '=', 'ward')]",
        required=True
    )

    @api.constrains('location_id')
    def _check_location_is_ward(self):
        for rec in self:
            if rec.location_id.type != 'ward':
                raise ValidationError("Location must have type = 'ward'.")

    def _get_location_full_path(self):
        """Hàm tiện ích lấy full_path của location mà không trigger field compute."""
        self.ensure_one()
        if self.location_id:
            return self.location_id.sudo().read(['full_path'])[0]['full_path']
        return ''

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        location_path = ''
        if rec.location_id:
            location_path = rec.location_id.sudo().read(['full_path'])[0]['full_path']
        full_path = " > ".join(filter(None, [
            location_path,
            rec.street or '',
            rec.house_number or '',
        ]))
        # Ghi trực tiếp full_path
        self.env.cr.execute("""
            UPDATE env_address SET full_path = %s WHERE id = %s
        """, (full_path, rec.id))
        return rec

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            location_path = ''
            if rec.location_id:
                location_path = rec.location_id.sudo().read(['full_path'])[0]['full_path']
            full_path = " > ".join(filter(None, [
                location_path,
                rec.street or '',
                rec.house_number or '',
            ]))
            self.env.cr.execute("""
                UPDATE env_address SET full_path = %s WHERE id = %s
            """, (full_path, rec.id))
        return res