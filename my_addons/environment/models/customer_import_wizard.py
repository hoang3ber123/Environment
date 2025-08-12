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

    def action_import_file(self):
        """Đọc CSV và in ra console"""
        if not self.file:
            raise UserError("Vui lòng tải file CSV.")

        # Giải mã file từ binary base64 -> text
        file_content = base64.b64decode(self.file)
        csv_text = file_content.decode('utf-8')

        # Đọc CSV thành list dict
        csv_reader = csv.DictReader(StringIO(csv_text))
        data = [row for row in csv_reader]

        # Tạo set chứa full_path location và collection_unit_id
        full_path_set = {row['location_id'] for row in data if row.get('location_id')}
        collection_unit_set = {row['collection_unit_id'] for row in data if row.get('collection_unit_id')}
        
        # ORM query env.location
        locations = self.env['env.location'].search([
            ('full_path', 'in', list(full_path_set))
        ])
        location_map = {loc.full_path: loc.id for loc in locations}

        # ORM query env.collectionunit
        collection_units = self.env['env.collectionunit'].search([
            ('code', 'in', list(collection_unit_set))
        ])
        collection_unit_map = {cu.code: cu.id for cu in collection_units}

        # Thay thế giá trị trong mảng data
        for row in data:
            loc_key = row.get('location_id')
            row['location_id'] = location_map.get(loc_key) if loc_key and loc_key in location_map else None

            cu_key = row.get('collection_unit_id')
            row['collection_unit_id'] = collection_unit_map.get(cu_key) if cu_key and cu_key in collection_unit_map else None
       

        # Tạo list vals để bulk create
        customer_vals_list = []
        for row in data:
            vals = {
                'name': row.get('name'),
                'code': row.get('code'),
                'customer_type': row.get('customer_type'),
                'phone': row.get('phone'),
                'email': row.get('email'),
                'cccd': row.get('cccd'),
                'waste_classification': bool(row.get('waste_classification')),
                'house_type': row.get('house_type'),
                'street': row.get('street'),
                'house_number': row.get('house_number'),
                'description': row.get('description'),
                'location_id': row.get('location_id'),
                'collection_unit_id': row.get('collection_unit_id'),
            }
        
            # Nếu bắt buộc field nào mà CSV không có → bỏ qua record
            if vals['name'] and vals['customer_type'] and vals['house_type'] and vals['street'] and vals['house_number'] and vals['location_id']:
                customer_vals_list.append(vals)

        # Bulk create
        if customer_vals_list:
            self.env['env.customer'].create(customer_vals_list)

        _logger.info("===== IMPORTED CUSTOMERS =====")
        _logger.info(customer_vals_list)


        return {'type': 'ir.actions.act_window_close'}
