from odoo import models, fields, api
class Service(models.Model):
    _name = 'env.service'
    _description = 'Service'
    _inherit = 'env.base'

    name = fields.Char(required=True, string="Name")
    code = fields.Char(required=True, string="Code")
    description = fields.Char(required=False, string="Description")
    scope = fields.Char(required=False, string="Scope")
    status = fields.Selection(
        selection=[('draft', 'Draft'), ('active', 'Active'), ('stopping', 'Stopping')],
        string="Status",
        default='draft'
    )
    groupservice_id = fields.Many2one('env.servicegroup', string='Group Service')

    @api.model
    def create(self, vals):
        name = vals.get('name', '')
        # Lấy ký tự đầu mỗi từ, viết hoa, giới hạn 5 ký tự
        code = ''.join([word[0].upper() for word in name.split() if word])[:5]
        vals['code'] = code
        return super().create(vals)