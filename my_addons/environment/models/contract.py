from odoo import api, fields, models
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from ..utils import permission

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
    start_date = fields.Date(string="Start Date", required=True, default=fields.Date.today)
    end_date = fields.Date(string="End Date", required=True)
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired')
    ], string="Status", default='active')

    contract_term = fields.Selection([
        ('6', '6 Tháng'),
        ('12', '12 Tháng'),
    ], string="Thời hạn (tháng)", required=True, default='12')

    months = fields.One2many('env.contract.month', 'contract_id', string='Contract Months')
    orders = fields.One2many('env.contract.order', 'contract_id', string='Orders')

    # compute field
    monthly_amount = fields.Float(
        string="Monthly Amount",
        compute="_compute_monthly_amount",
        store=True,
        readonly=True
    )
    months_paid_count = fields.Integer(
        string="Số tháng đã đóng",
        compute="_compute_months_paid_count",
        store=True
    )
    orders_count = fields.Integer(
        string="Số hóa đơn",
        compute="_compute_orders_count",
        store=True
    )
    progress_percent = fields.Float(
        string="Tiến độ (%)",
        compute="_compute_progress",
        store=True
    )
    remaining_debt = fields.Float(
        compute="_compute_remaining_debt", 
        string="Nợ còn lại", 
        store=True
    )

    # ========== TÍNH TOÁN CHO CÁC FIELD COMPUTE ===============
    # Tính toán tiền trong tháng phải trả
    @api.depends(
        "collection_unit_id",
        "service_id",
        "customer_waste_group_id",
        "estimated_waste_volume",
        "service_id.serviceprice_ids",
        "service_id.serviceprice_ids.component_ids",
        "collection_unit_id.unitserviceprice_ids.multiplier",
    )
    def _compute_monthly_amount(self):
        for rec in self: 
            if not (rec.collection_unit_id and rec.service_id and rec.customer_waste_group_id):
                rec.monthly_amount = 0.0
                continue

            service_price = self.env['env.serviceprice'].search([
                ('service_id', '=', rec.service_id.id),
                ('customerwastegroup_id', '=', rec.customer_waste_group_id.id)
            ], limit=1)
            
            if not service_price:
                rec.monthly_amount = 0.0
                continue

            unit_service_price = self.env['env.unitserviceprice'].search([
                ('collection_unit_id', '=', rec.collection_unit_id.id),
                ('service_price_id', '=', service_price.id)
            ], limit=1)
 
            multiplier = unit_service_price.multiplier if unit_service_price else 1.0

            components = self.env['env.servicepricecomponent'].search([
                ('service_price_id', '=', service_price.id)
            ])

            total = 0.0
            for comp in components:
                if comp.unit == 'month':
                    total += comp.amount * multiplier
                elif comp.unit == 'kg':
                    total += comp.amount * multiplier * rec.estimated_waste_volume

            rec.monthly_amount = total

    # Tính số lượng tháng đã trả
    @api.depends("months.paid")
    def _compute_months_paid_count(self):
        for rec in self:
            rec.months_paid_count = len(rec.months.filtered(lambda m: m.paid))

    # Tính số lượng hóa đơn đã thanh toán
    @api.depends("orders")
    def _compute_orders_count(self):
        for rec in self:
            rec.orders_count = len(rec.orders)

    # Tính tiến độ hoàn thành hợp đồng
    @api.depends("contract_term", "months_paid_count")
    def _compute_progress(self):
        for rec in self:
            if rec.contract_term:
                try:
                    term = int(rec.contract_term)
                except ValueError:
                    term = 0
                rec.progress_percent = (rec.months_paid_count / term * 100) if term else 0
            else:
                rec.progress_percent = 0

    # Tính toán công nợ còn lại
    @api.depends("monthly_amount", "contract_term", "orders", "orders")
    def _compute_remaining_debt(self):
        for rec in self:
            try:
                term = int(rec.contract_term)
            except ValueError:
                term = 0
            total_value = rec.monthly_amount * term
            paid_value = sum(order.total_amount for order in rec.orders)
            rec.remaining_debt = total_value - paid_value

    # ========== ACTION TRÊN FIELD ===============
    @api.onchange('start_date', 'contract_term')
    def _onchange_date_or_term(self):
        if self.start_date and self.contract_term:
            self.end_date = self._calc_end_date(self.start_date, self.contract_term)
        else:
            self.end_date = False

    # Khi thay đổi customer_id thì chọn luôn collection unit
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id and self.customer_id.collection_unit_id:
            self.collection_unit_id = self.customer_id.collection_unit_id
        else:
            self.collection_unit_id = False
        self.service_id = False
    
    # Khi đổi collection_unit -> lọc lại service
    @api.onchange('collection_unit_id')
    def _onchange_collection_unit_id(self):
        self.service_id = False
        self.customer_waste_group_id = False
        domain = []
        if self.collection_unit_id:
            unit_services = self.env['env.unitservice'].search([
                ('collection_unit_id', '=', self.collection_unit_id.id)
            ])
            service_ids = unit_services.mapped('service_id').ids
            domain = [('id', 'in', service_ids)]
        return {'domain': {'service_id': domain}}

    # Khi đổi service -> lọc lại customer_waste_group
    @api.onchange('service_id')
    def _onchange_service_id(self):
        self.customer_waste_group_id = False
        domain = []
        if self.collection_unit_id and self.service_id:
            # Tìm service_price hợp lệ
            service_prices = self.env['env.serviceprice'].search([
                ('service_id', '=', self.service_id.id),
            ])
            # Giữ lại waste_group mà có UnitServicePrice cho collection_unit hiện tại
            valid_groups = []
            for sp in service_prices:
                unit_price = self.env['env.unitserviceprice'].search([
                    ('collection_unit_id', '=', self.collection_unit_id.id),
                    ('service_price_id', '=', sp.id)
                ], limit=1)
                if unit_price:
                    valid_groups.append(sp.customerwastegroup_id.id)

            domain = [('id', 'in', valid_groups)]
        return {'domain': {'customer_waste_group_id': domain}}

    # ========== VALIDATE & HELPER DỮ LIỆU ===============
    # Check xem service có thuộc sở hữu của đơn vị thu gom không?
    @api.onchange('collection_unit_id', 'service_id')
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

    # Check xem thử là customer waste có liên kết với service thông qua price không?
    @api.onchange('service_id', 'customer_waste_group_id', 'collection_unit_id')
    def _check_waste_group_in_service_price(self):
        for rec in self:
            if rec.service_id and rec.customer_waste_group_id:
                # 1. Kiểm tra Service + Waste Group trong bảng giá dịch vụ
                service_price = self.env['env.serviceprice'].search([
                    ('service_id', '=', rec.service_id.id),
                    ('customerwastegroup_id', '=', rec.customer_waste_group_id.id)
                ], limit=1)

                if not service_price:
                    raise ValidationError(
                        f"Nhóm nguồn thải '{rec.customer_waste_group_id.name}' "
                        f"không có trong bảng giá cho dịch vụ '{rec.service_id.name}'."
                    )

                # 2. Kiểm tra đơn vị thu gom có bảng giá này không
                unit_service_price = self.env['env.unitserviceprice'].search([
                    ('collection_unit_id', '=', rec.collection_unit_id.id),
                    ('service_price_id', '=', service_price.id)
                ], limit=1)

                if not unit_service_price:
                    raise ValidationError(
                        f"Đơn vị thu gom '{rec.collection_unit_id.name}' "
                        f"không có bảng giá nào cho nhóm nguồn thải '{rec.customer_waste_group_id.name}'."
                    )

    def _calc_end_date(self, start_date, contract_term):
        """Helper: tính ngày hết hạn"""
        if not start_date or not contract_term:
            return None
        if isinstance(start_date, str):
            start_date = fields.Date.from_string(start_date)
        if contract_term == '6':
            return start_date + relativedelta(months=6)
        elif contract_term == '12':
            return start_date + relativedelta(months=12)
        return None
    
    def _init_months(self):
        """Tạo các bản ghi env.contract.month cho hợp đồng nếu chưa có"""
        for rec in self:
            if rec.months:
                continue  # đã có thì bỏ qua
            term_months = int(rec.contract_term)
            start_month = rec.start_date.month
            for i in range(1, term_months + 1):
                month_num = (start_month + i - 1) % 12 or 12
                self.env["env.contract.month"].create({
                    "contract_id": rec.id,
                    "name": str(month_num),
                    "paid": False
                })

    # ========== TẠO VÀ CẬP NHẬT DỮ LIỆU ===============
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Cập nhật collection_unit_id dựa trên customer_id
            if 'customer_id' in vals and not vals.get('collection_unit_id'):
                customer = self.env['env.customer'].browse(vals['customer_id'])
                if customer.collection_unit_id:
                    collection_unit_id = customer.collection_unit_id.id
                    vals['collection_unit_id'] = customer.collection_unit_id.id
            
            # check quyền
            if collection_unit_id:
                permission.check_employee_permission(self.env, collection_unit_id, "add_contract")
            
            # Đảm bảo start_date
            vals.setdefault("start_date", fields.Date.today())

            # Đảm bảo contract_term
            vals.setdefault("contract_term", "12")

            # Tính end_date trước khi tạo record
            vals['end_date'] = self._calc_end_date(vals['start_date'], vals['contract_term'])

        # Tạo records
        records = super().create(vals_list)

        # Tạo các ContractMonth
        records._init_months()

        return records

    def write(self, vals):
        blocked_fields = {
            "customer_id", "collection_unit_id", "service_id",
            "customer_waste_group_id", "contract_term",
            "start_date", "end_date"
        }

        for rec in self:
            # check quyền
            collection_unit_id = vals.get("collection_unit_id", rec.collection_unit_id.id)
            permission.check_employee_permission(self.env, collection_unit_id, "edit_contract")
            
            # Check tháng đã trả chưa
            if rec.months and any(m.paid for m in rec.months):
                # Nếu có tháng đã thanh toán → chặn update các field nhạy cảm
                for field in blocked_fields:
                    if field in vals:
                        raise ValidationError(
                            f"Không thể chỉnh sửa trường '{field}' vì hợp đồng đã có tháng được thanh toán."
                        )

            # Set mặc định nếu chưa có start_date
            start_date = vals.get("start_date", rec.start_date or fields.Date.today())
            contract_term = vals.get("contract_term", rec.contract_term or 12)

            # Cập nhật end_date khi có thay đổi start_date hoặc contract_term
            start_date = vals.get("start_date", rec.start_date)
            contract_term = vals.get("contract_term", rec.contract_term)
            vals["end_date"] = self._calc_end_date(start_date, contract_term)

            # Nếu đổi customer_id thì gán collection_unit_id tự động
            if "customer_id" in vals and not vals.get("collection_unit_id"):
                customer = self.env["env.customer"].browse(vals["customer_id"])
                if customer.collection_unit_id:
                    vals["collection_unit_id"] = customer.collection_unit_id.id

        res = super().write(vals)

        # Nếu chưa có months thì khởi tạo
        self._init_months()

        return res

