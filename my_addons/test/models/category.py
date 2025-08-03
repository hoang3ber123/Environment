# models/category.py
from odoo import models, fields
class Category(models.Model):
    _name = "env.category"
    _description = "Category"
    _inherit = 'env.base'

    name = fields.Char(required=True)
    description = fields.Char(required=True)