from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


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
    months_paid = fields.Integer(
        string="Số tháng thanh toán",
        required=True,
        default=1
    )
    total_amount = fields.Float(
        string="Tổng tiền thanh toán",
        compute="_compute_total_amount",
        store=True,
        readonly=True
    )

    # Quan hệ ngược từ Contract -> Orders
    # (đặt bên Contract để dễ xem, bạn có thể thêm vào model Contract luôn)
    # orders = fields.One2many("env.contract.order", "contract_id", string="Orders")

    @api.depends("months_paid", "contract_id.monthly_amount")
    def _compute_total_amount(self):
        for rec in self:
            if rec.contract_id and rec.months_paid > 0:
                rec.total_amount = rec.months_paid * rec.contract_id.monthly_amount
            else:
                rec.total_amount = 0.0

    @api.constrains("months_paid", "contract_id")
    def _check_months_paid(self):
        for rec in self:
            if rec.months_paid <= 0:
                raise ValidationError("Số tháng thanh toán phải lớn hơn 0.")

            if rec.contract_id:
                # Tổng số tháng đã thanh toán cho contract này (chưa tính record hiện tại)
                already_paid = sum(
                    rec.contract_id.orders.filtered(lambda o: o.id != rec.id).mapped("months_paid")
                )
                try:
                    contract_term = int(rec.contract_id.contract_term or 0)
                except ValueError:
                    contract_term = 0

                if already_paid + rec.months_paid > contract_term:
                    raise ValidationError(
                        f"Tổng số tháng thanh toán ({already_paid + rec.months_paid}) vượt quá thời hạn hợp đồng {contract_term} tháng."
                    )
                