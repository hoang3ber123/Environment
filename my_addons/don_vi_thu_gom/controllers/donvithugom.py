from odoo import http
from odoo.http import request

class DonViThuGomController(http.Controller):

    @http.route('/donvithugom/list', type='json', auth='user')
    def donvithugom_list(self, name=None, title=None):
        domain = []
        if name:
            domain.append(('name', 'ilike', name))
        if title:
            domain.append(('title', 'ilike', title))

        records = request.env['donvithugom.model'].search(domain)
        return [{'id': r.id, 'name': r.name, 'title': r.title, 'address': r.address } for r in records]

    @http.route('/donvithugom/create', type='json', auth='user')
    def donvithugom_create(self, **kwargs):
        name = kwargs.get('name')
        title = kwargs.get('title')
        address = kwargs.get('address')
        if not name:
            return {'error': 'Missing name'}
        if not title:
            return {'error': 'Missing title'}
        if not address:
            return {'error': 'Missing address'}
        record = request.env['donvithugom.model'].create({'name': name,'title':title, 'address':address})
        return {'id': record.id, 'name': record.name, 'title': record.title, 'address': record.address }
    
    @http.route('/donvithugom/delete_bulk', type='json', auth='user', csrf=False)
    def delete_bulk(self, ids):
        # Kiểm tra xem ids có phải là một list có thể hiểu là kiểm tra xem ids có phải mảng hay không hay không ?
        if not isinstance(ids, list):
            return {"error": "Invalid data format"}

        records = request.env['donvithugom.model'].browse(ids)
        records.unlink()

        return {"status": "success", "deleted_ids": ids}

    @http.route('/donvithugom/detail', type='json', auth='user', csrf=False)
    def donvithugom_detail(self, id):
        record = request.env['donvithugom.model'].browse(id)
        if not record.exists():
            return {'error': 'Record not found'}
        return {
            'id': record.id,
            'name': record.name,
            'title': record.title,
            'address': record.address,
            'create_date': str(record.create_date),
        }

    @http.route('/donvithugom/update', type='json', auth='user', csrf=False)
    def donvithugom_update(self, id, **kwargs):
        if not id:
            return {"error": "Missing id"}

        # lấy record với id truyền vào để update
        record = request.env['donvithugom.model'].browse(id)

        # kiểm tra nếu như mà không có quyền thì thông báo lỗi
        if not record.exists():
            return {"error": "Record not found"}

        # update dòng vừa lấy ra
        # Lấy các field từ kwargs
        name = kwargs.get('name')
        title = kwargs.get('title')
        address = kwargs.get('address')
        update_values = {}

        if name is not None:
            update_values['name'] = name

        if title is not None:
            update_values['title'] = title

        if address is not None:
            update_values['address'] = address
        
        # update kiểm tra xem có trường nào cần update không
        if update_values:
            # thực hiện update vào cơ sở dữ liệu
            record.write(update_values)
            return {"status": "success"}
        else:
            return {"status": "no_update", "message": "No fields to update"}

