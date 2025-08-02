from odoo import models, fields

class Test(models.Model):
    _name = 'test.model'
    _description = 'Hello test'

    name = fields.Char(string="Name")
    title = fields.Char(string="Title")
<<<<<<< HEAD
=======
    image = fields.Binary(string="Image", attachment=True)
>>>>>>> a7a2e8c (feature: save state)
