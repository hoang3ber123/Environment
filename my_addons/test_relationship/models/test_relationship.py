from odoo import models, fields

class TestRelationship(models.Model):
    _name = 'test_relationship.model'
    _description = 'Hello test1'

    name = fields.Char(string="Name")
