from odoo import api, fields, models
from odoo.exceptions import ValidationError
from ..utils import permission

class ContractOrder(models.Model):
    _name = "env.contract.order"
    _description = "Contract Order"
    _inherit = 'env.base'

    contract_id = fields.Many2one(
        "env.contract",
        string="Contract",
        required=True,
        ondelete="cascade"
    )
    months_selected = fields.Many2many(
        'env.contract.month',
        string="Tháng thanh toán",
        domain="[('contract_id','=',contract_id),('paid','=',False)]"
    )
    total_amount = fields.Float(
        string="Tổng tiền thanh toán",
        compute="_compute_total_amount",
        store=True,
        readonly=True
    )

    @api.depends("months_selected", "contract_id.monthly_amount")
    def _compute_total_amount(self):
        for rec in self:
            if rec.contract_id:
                rec.total_amount = len(rec.months_selected) * rec.contract_id.monthly_amount
            else:
                rec.total_amount = 0.0

    @api.constrains("months_selected", "contract_id")
    def _check_months_selected(self):
        for rec in self:
            if not rec.months_selected:
                raise ValidationError("Phải chọn ít nhất 1 tháng để thanh toán.")

            # Kiểm tra xem các tháng đã chọn thuộc hợp đồng
            for month in rec.months_selected:
                if month.contract_id != rec.contract_id:
                    raise ValidationError(f"Tháng {month.name} không thuộc hợp đồng này.")

    @api.model
    def create(self, vals):
        # check quyền
        contract = self.env["env.contract"].browse(vals.get("contract_id"))
        if contract and contract.collection_unit_id:
            permission.check_employee_permission(
                self.env, contract.collection_unit_id.id, "create_order"
            )
        order = super().create(vals)
        # Đánh dấu các tháng đã thanh toán
        for month in order.months_selected:
            month.paid = True
            month.order_id = order.id
        return order
    
    def write(self, vals):
        for rec in self:
            contract = rec.contract_id
            if contract and contract.collection_unit_id:
                permission.check_employee_permission(
                    self.env, contract.collection_unit_id.id, "edit_contract"
                )
        return super().write(vals)

class ContractMonth(models.Model):
    _name = 'env.contract.month'
    _description = 'Contract Month'

    name = fields.Char(string='Month')
    contract_id = fields.Many2one('env.contract', string='Contract', ondelete='cascade')
    paid = fields.Boolean(string='Paid', default=False)
    order_id = fields.Many2one('env.contract.order', string='Related Order')
