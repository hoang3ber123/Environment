from odoo import models, fields
class Tag(models.Model):
    _name = 'env.tag'
    _description = 'Tag'
    _inherit = 'env.base'

    name = fields.Char(required=True)
    description = fields.Char(required=True)
    test_id = fields.Many2one('env.test', string='Test')