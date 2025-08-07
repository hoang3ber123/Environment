from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Address(models.Model):
    _name = 'env.address'
    _description = 'Địa chỉ'
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
        string="Loại nhà",
        required=True,
        help="Chọn loại hình nhà ở tương ứng với địa chỉ này."
    )

    street = fields.Char(
        required=True, 
        string="Tên đường",
        help="Nhập tên đường hoặc tuyến đường (VD: Nguyễn Văn Cừ, Trần Hưng Đạo...)"
        )
    
    house_number = fields.Char(
        required=True,
        string="Số nhà",
        help="Nhập số nhà cụ thể (VD: 123A, 45/2B...)."
    )

    description = fields.Text(
        string="Mô tả",
        help="Ghi chú thêm về địa chỉ nếu cần (VD: gần chợ, sau lưng trường học...)."
    )

    full_path = fields.Char(
        string="Đường dẫn đầy đủ",
        readonly=True,
        help="Thông tin địa chỉ đầy đủ được kết hợp từ vị trí, tên đường và số nhà. Tự động sinh."
    )

    location_id = fields.Many2one(
        comodel_name='env.location',
        string="Vị trí (Chỉ Phường/Xã)",
        domain="[('type', '=', 'ward')]",
        required=True,
        help="Chọn Phường/Xã tương ứng với địa chỉ. Bắt buộc là loại 'ward'."
    )

    @api.constrains('location_id')
    def _check_location_is_ward(self):
        for rec in self:
            if rec.location_id.type != 'ward':
                raise ValidationError("Vị trí được chọn phải có loại là 'ward' (Phường/Xã).")

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