from odoo import models, fields

class Test(models.Model):
    _name = 'test.model'
    _description = 'Hello test'

    name = fields.Char(string="Name")
    title = fields.Char(string="Title")
    image = fields.Binary(string="Image", attachment=True)
