from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class Contract(models.Model):
    _name = "env.contract"
    _description = "Contract"

    contract_number = fields.Char(string="Contract Number", required=True)
    customer_id = fields.Many2one("env.customer", string="Customer", required=True)
    collection_unit_id = fields.Many2one(
        "env.collectionunit",
        string="Collection Unit",
        required=True,
        readonly=True,
    )
    service_id = fields.Many2one("env.service", string="Service", required=True)
    customer_waste_group_id = fields.Many2one(
        "env.customerwastegroup",
        string="Nhóm nguồn thải",
        required=True,
    )
    estimated_waste_volume = fields.Float(string="Estimated Waste Volume")
    employee_id = fields.Many2one("res.users", string="Created By")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired')
    ], string="Status", default='active')

    monthly_amount = fields.Float(
        string="Monthly Amount",
        compute="_compute_monthly_amount",
        store=True,
        readonly=True
    )
    total_amount = fields.Float(string="Total Amount", default=0.0, readonly=True)

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id and self.customer_id.collection_unit_id:
            self.collection_unit_id = self.customer_id.collection_unit_id
        else:
            self.collection_unit_id = False
        self.service_id = False  # reset service khi đổi customer

    @api.onchange('collection_unit_id')
    def _onchange_collection_unit_id(self):
        domain = []
        if self.collection_unit_id:
            unit_services = self.env['env.unitservice'].search([
                ('collection_unit_id', '=', self.collection_unit_id.id)
            ])
            service_ids = unit_services.mapped('service_id').ids
            domain = [('id', 'in', service_ids)]
        return {'domain': {'service_id': domain}}

    def _check_service_in_unit(self):
        for rec in self:
            if rec.collection_unit_id and rec.service_id:
                unit_service = self.env['env.unitservice'].search([
                    ('collection_unit_id', '=', rec.collection_unit_id.id),
                    ('service_id', '=', rec.service_id.id)
                ], limit=1)
                if not unit_service:
                    raise ValidationError(
                        f"Dịch vụ '{rec.service_id.name}' không thuộc đơn vị '{rec.collection_unit_id.name}'."
                    )

    def _check_waste_group_in_service_price(self):
        for rec in self:
            if rec.service_id and rec.customer_waste_group_id:
                service_price = self.env['env.serviceprice'].search([
                    ('service_id', '=', rec.service_id.id),
                    ('customerwastegroup_id', '=', rec.customer_waste_group_id.id)
                ], limit=1)
                if not service_price:
                    raise ValidationError(
                        f"Nhóm nguồn thải '{rec.customer_waste_group_id.name}' không hợp lệ cho dịch vụ '{rec.service_id.name}'."
                    )

    @api.depends('collection_unit_id', 'service_id', 'customer_waste_group_id', 'estimated_waste_volume')
    def _compute_monthly_amount(self):
        for rec in self:
            _logger.info("=== Start compute monthly_amount for Contract ID %s ===", rec.id)
            _logger.info("Collection Unit: %s, Service: %s, Waste Group: %s, Estimated Volume: %s",
            rec.collection_unit_id.id, rec.service_id.id, rec.customer_waste_group_id.id, rec.estimated_waste_volume)
            
            if not (rec.collection_unit_id and rec.service_id and rec.customer_waste_group_id):
                _logger.warning("Missing required fields for calculation.")
                rec.monthly_amount = 0.0
                continue

            service_price = self.env['env.serviceprice'].search([
                ('service_id', '=', rec.service_id.id),
                ('customerwastegroup_id', '=', rec.customer_waste_group_id.id)
            ], limit=1)
            _logger.info("Service Price found: %s", service_price.id)
            
            if not service_price:
                _logger.warning("No service_price found.")
                rec.monthly_amount = 0.0
                continue

            unit_service_price = self.env['env.unitserviceprice'].search([
                ('collection_unit_id', '=', rec.collection_unit_id.id),
                ('service_price_id', '=', service_price.id)
            ], limit=1)

            _logger.info("Unit Service Price found: %s, Multiplier: %s",
                     unit_service_price.id, unit_service_price.multiplier if unit_service_price else None)
            
            multiplier = unit_service_price.multiplier if unit_service_price else 1.0

            components = self.env['env.servicepricecomponent'].search([
                ('service_price_id', '=', service_price.id)
            ])
            _logger.info("Found %s components", len(components))

            total = 0.0
            for comp in components:
                _logger.info("Component: %s, Amount: %s, Unit: %s",
                         comp.id, comp.amount, comp.unit)
                if comp.unit == 'month':
                    total += comp.amount * multiplier
                elif comp.unit == 'kg':
                    total += comp.amount * multiplier * rec.estimated_waste_volume

            rec.monthly_amount = total
            _logger.info("Final monthly_amount: %s", rec.monthly_amount)
            _logger.info("=== End compute monthly_amount ===")

    @api.model
    def create(self, vals):
        if 'customer_id' in vals and not vals.get('collection_unit_id'):
            customer = self.env['env.customer'].browse(vals['customer_id'])
            if customer.collection_unit_id:
                vals['collection_unit_id'] = customer.collection_unit_id.id

        record = super().create(vals)
        record._check_service_in_unit()
        record._check_waste_group_in_service_price()
        return record

    def write(self, vals):
        res = super().write(vals)
        self._check_service_in_unit()
        self._check_waste_group_in_service_price()
        return res
