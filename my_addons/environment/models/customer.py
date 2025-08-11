from odoo import models, fields, api
from odoo.exceptions import ValidationError

class Customer(models.Model):
    _name = 'env.customer'
    _description = 'Khách hàng'
    _inherit = 'env.base'

    name = fields.Char(
        string="Tên khách hàng",
        required=True,
        help="Tên khách hàng (VD: Hộ gia đình, Công ty Cổ phần ABC)."
    )

    code = fields.Char(
        string="Mã khách hàng",
        help="Mã định danh duy nhất của khách hàng (nếu có)"
    )

    customer_type = fields.Selection(
        selection=[
            ('CN', 'Cá nhân'),
            ('TC', 'Tổ chức'),
            ('HGD', 'Hộ gia đình'),
            ('N1', 'Nhóm 1'),
            ('N2', 'Nhóm 2'),
            ('N3', 'Nhóm 3'),
            ('N4', 'Nhóm 4'),
        ],
        string="Loại khách hàng",
        required=True,
        help="Chọn loại khách hàng: Cá nhân, Tổ chức, Hộ gia đình hoặc Nhóm 1-4."
    )

    phone = fields.Char(
        string="Số điện thoại",
        size=20,
        help="Số điện thoại liên hệ của khách hàng."
    )

    email = fields.Char(
        string="Email",
        help="Địa chỉ email liên hệ của khách hàng."
    )

    cccd = fields.Char(
        string="CCCD",
        size=20,
        help="Căn cước công dân của khách hàng (nếu có)."
    )

    waste_classification = fields.Boolean(
        string="Phân loại rác",
        default=False,
        required=True,
        help="Phân loại rác"
    )

    house_type = fields.Selection(
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

    collection_unit_id = fields.Many2one(
        comodel_name='env.collectionunit',
        string="Đơn vị thu gom",
        required=False,
        ondelete='restrict',
        help="Đơn vị thu gom phụ trách khách hàng này."
    )

    # ==== Ràng buộc ====
    _sql_constraints = [
        ('name_uniq', 'unique(name, type)', 'Tên khách hàng và loại khách hàng phải là duy nhất.'),
        ('phone_uniq', 'unique(phone)', 'Số điện thoại đã tồn tại.'),
        ('email_uniq', 'unique(email)', 'Email đã tồn tại.'),
        ('cccd_uniq', 'unique(cccd)', 'CCCD đã tồn tại.'),
        ('code_uniq', 'unique(code)', 'Mã khách hàng phải là duy nhất.')
    ]

    @api.constrains('location_id')
    def _check_location_is_ward(self):
        for rec in self:
            if rec.location_id.type != 'ward':
                raise ValidationError("Vị trí được chọn phải có loại là 'ward' (Phường/Xã).")

    @api.constrains('collection_unit_id', 'location_id')
    def _check_collection_unit_location_scope(self):
        for rec in self:
            if rec.collection_unit_id and rec.location_id:
                customer_path = rec.location_id.full_path or ''
                # Lấy tất cả full_path của các location mà CollectionUnit quản lý
                managed_paths = rec.collection_unit_id.location_ids.mapped('full_path')

                # Check xem customer_path có bắt đầu bằng bất kỳ managed_path nào không
                is_valid = any(customer_path.startswith(mp) for mp in managed_paths)

                if not is_valid:
                    raise ValidationError(
                        "Đơn vị thu gom '%s' không phụ trách khu vực '%s'."
                        % (rec.collection_unit_id.name, rec.location_id.full_path)
                    )

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
            UPDATE env_customer SET full_path = %s WHERE id = %s
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
                UPDATE env_customer SET full_path = %s WHERE id = %s
            """, (full_path, rec.id))
        return res  