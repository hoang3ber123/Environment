from odoo import models, fields

class donvithugom(models.Model):
    _name = 'donvithugom.model'
    _description = 'DonVI hello'

    name = fields.Char(string="Name")
    title = fields.Char(string="Title")
    address = fields.Char(string="Address")
    created_at = fields.Datetime(string="Created At", default=fields.Datetime.now)
