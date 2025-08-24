from odoo import models, fields, api


class UnitServicePrice(models.Model):
    _name = 'env.unitserviceprice'
    _description = 'Unit Service Price'
    _inherit = 'env.base'

    collection_unit_id = fields.Many2one(
        'env.collectionunit',
        string='Unit',
        required=True,
        ondelete='cascade'
    )

    service_price_id = fields.Many2one(
        'env.serviceprice',
        string='Service Price',
        required=True,
        ondelete='cascade'
    )

    multiplier = fields.Float(
        string='Multiplier',
        default=1.0,
        required=True
    )

    effective_from = fields.Date(
        string='Effective From',
        required=True
    )

    effective_to = fields.Date(
        string='Effective To',
        required=True
    )

    status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        string='Status',
        default='active',
        required=True
    )

    _sql_constraints = [
        (
            'unit_service_price_unique',
            'unique(collection_unit_id, service_price_id, effective_from, effective_to)',
            'Một đơn vị và bảng giá dịch vụ chỉ được cấu hình 1 lần cho cùng khoảng thời gian!'
        )
    ]

    @api.onchange('multiplier')
    def _check_multiplier(self):
        if self.multiplier <= 0:
            return {
                'warning': {
                    'title': "Invalid Multiplier",
                    'message': "Multiplier phải lớn hơn 0."
                }
            }