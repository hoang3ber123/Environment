from odoo import models, fields, api

class Location(models.Model):
    _name = 'env.location'
    _description = 'Location'
    _inherit = 'env.base'
    
    name = fields.Char(required=True, string="Name", readonly=True)
    
    type = fields.Selection(
        selection=[
            ('province', 'Tỉnh / Thành phố'), 
            ('district', 'Quận / Huyện'), 
            ('ward', 'Phường / Xã'),
        ],
        string="Type",
        default='province',
        required=True
    )

    code = fields.Char(required=True, string="Code", readonly=True)
    
    # full_path sẽ được import/gán cứng từ đầu
    full_path = fields.Char(required=True, string="Full Path", readonly=True)

    parent_id = fields.Many2one('env.location', string='Parent Location', readonly=True)

    name_get = lambda self: [(rec.id, rec.full_path) for rec in self]

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|', ('full_path', operator, name), ('name', operator, name)] + args
        return self.search(args, limit=limit).name_get()