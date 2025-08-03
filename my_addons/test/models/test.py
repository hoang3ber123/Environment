from odoo import models, fields

class Test(models.Model):
    _name = 'env.test'
    _description = 'Hello test'
    _inherit = 'env.base'
    # === Basic Fields ===
    name = fields.Char(string="Name")  # Chuỗi ngắn
    title = fields.Char(string="Title")
    age = fields.Integer(string="Age")  # Số nguyên
    score = fields.Float(string="Score")  # Số thực
    is_active = fields.Boolean(string="Is Active")  # Checkbox
    birthday = fields.Date(string="Birthday")  # Ngày
    checkin = fields.Datetime(string="Check-in Time")  # Ngày giờ
    status = fields.Selection(  # Dropdown cố định
        selection=[('draft', 'Draft'), ('done', 'Done')],
        string="Status",
        default='draft'
    )
    notes = fields.Html(string="Notes")  # Rich text
    image = fields.Binary(string="Image", attachment=True)  # Ảnh upload

    # tiền tệ thì phải tải cái module có sẵn về tiền tệ của odoo rồi liên kết
    currency_id = fields.Many2one('res.currency', string="Currency")  # Tiền tệ
    amount = fields.Monetary(string="Amount", currency_field='currency_id')  # Số tiền

    # === Relational Fields ===

    # === One to Many
    tag_ids = fields.One2many('env.tag', 'test_id', string='Tags')
    
    # === Many to Many
    category_ids = fields.Many2many('env.category', string='Categories')