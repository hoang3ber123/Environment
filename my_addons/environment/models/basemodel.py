from odoo import models, fields, api

class BaseModel(models.AbstractModel):
    _name = 'env.base'
    _description = 'Base model with created_at, updated_at'

    created_at = fields.Datetime(string='Created At', readonly=True)
    updated_at = fields.Datetime(string='Updated At', readonly=True)
    created_by = fields.Many2one('res.users', string='Created By', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['created_at'] = fields.Datetime.now()
            vals['updated_at'] = fields.Datetime.now()
            vals['created_by'] = self.env.uid
        return super().create(vals_list)

    def write(self, vals):
        vals['updated_at'] = fields.Datetime.now()
        return super().write(vals)