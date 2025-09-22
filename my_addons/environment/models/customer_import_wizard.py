import base64
import csv
from io import StringIO
import logging
from odoo import models, fields
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class CustomerImportWizard(models.TransientModel):
    _name = 'env.customerimportwizard'
    _description = 'Import Customer from Excel'

    file = fields.Binary(string="File Excel", required=True)
    filename = fields.Char(string="Tên file")

    # Thêm field chọn sẵn
    collection_unit_id = fields.Many2one(
        'env.collectionunit',
        string="Đơn vị thu gom",
        required=True,
        help="Chọn đơn vị thu gom áp dụng cho toàn bộ khách hàng trong file."
    )
    location_id = fields.Many2one(
        'env.location',
        string="Địa phương",
        required=True,
        help="Chọn địa phương áp dụng cho toàn bộ khách hàng trong file."
    )

    def action_import_file(self):
        if not self.file:
            raise UserError("Vui lòng tải file CSV.")

        # Check location phải là ward
        if self.location_id.type != 'ward':
            raise UserError("Vị trí được chọn phải có loại là 'ward' (Phường/Xã).")

        # Check collection_unit có quản lý location không
        customer_path = self.location_id.full_path or ''
        managed_paths = self.collection_unit_id.location_ids.mapped('full_path')
        is_valid = any(customer_path.startswith(mp) for mp in managed_paths)
        if not is_valid:
            raise UserError(
                "Đơn vị thu gom '%s' không phụ trách khu vực '%s'."
                % (self.collection_unit_id.name, self.location_id.full_path)
            )

        # Giải mã file từ binary base64 -> text
        file_content = base64.b64decode(self.file)
        csv_text = file_content.decode('utf-8')

        csv_reader = csv.DictReader(StringIO(csv_text))
        data = [row for row in csv_reader]

        customer_vals_list = []
        for row in data:
            vals = {
                'name': row.get('name'),
                'code': row.get('code'),
                'customer_type': row.get('customer_type'),
                'phone': row.get('phone'),
                'email': row.get('email'),
                'cccd': row.get('cccd'),
                'waste_classification': str(row.get('waste_classification')).strip().lower() in ['true', '1', 'yes'],
                'house_type': row.get('house_type'),
                'street': row.get('street'),
                'house_number': row.get('house_number'),
                'description': row.get('description'),
                'location_id': self.location_id.id,
                'collection_unit_id': self.collection_unit_id.id,
            }
            if vals['name'] and vals['customer_type'] and vals['house_type'] and vals['street'] and vals['house_number']:
                customer_vals_list.append(vals)

        if customer_vals_list:
            self.env['env.customer'].create(customer_vals_list)

        _logger.info("===== IMPORTED CUSTOMERS =====")
        _logger.info(customer_vals_list)

        return {'type': 'ir.actions.act_window_close'}
