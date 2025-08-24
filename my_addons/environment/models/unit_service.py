from odoo import models, fields, api
class UnitServiceRel(models.Model):
    _name = 'env.unitservice'
    _description = 'Liên kết Đơn vị thu gom - Dịch vụ'

    collection_unit_id = fields.Many2one(
        'env.collectionunit',
        string='Collection Unit',
        required=True,
        ondelete='cascade'
    )
    service_id = fields.Many2one(
        'env.service',
        string='Service',
        required=True,
        ondelete='cascade'
    )
    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        string='Status',
        default='active',
        required=True
    )

    _sql_constraints = [
        (
            'unit_service_unique',
            'unique(collection_unit_id, service_id)',
            'Một đơn vị và dịch vụ chỉ được liên kết một lần!'
        )
    ]