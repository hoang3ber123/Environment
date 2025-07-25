from odoo import http
from odoo.http import request

class TestController(http.Controller):

    @http.route('/test/list', type='json', auth='user')
    def test_list(self, name=None):
        domain = []
        if name:
            domain.append(('name', 'ilike', name))

        records = request.env['test.model'].search(domain)
        return [{'id': r.id, 'name': r.name, 'title': r.title} for r in records]

    @http.route('/test/create', type='json', auth='user')
    def test_create(self, **kwargs):
        name = kwargs.get('name')
        title = kwargs.get('title')
        if not name:
            return {'error': 'Missing name'}
        if not title:
            return {'error': 'Missing title'}
        record = request.env['test.model'].create({'name': name,'title':title})
        return {'id': record.id, 'name': record.name, 'title': record.title }
    
    @http.route('/test/delete_bulk', type='json', auth='user', csrf=False)
    def delete_bulk(self, ids):
        # Kiểm tra xem ids có phải là một list có thể hiểu là kiểm tra xem ids có phải mảng hay không hay không ?
        if not isinstance(ids, list):
            return {"error": "Invalid data format"}

        records = request.env['test.model'].browse(ids)
        records.unlink()

        return {"status": "success", "deleted_ids": ids}

    @http.route('/test/detail', type='json', auth='user', csrf=False)
    def test_detail(self, id):
        record = request.env['test.model'].browse(id)
        if not record.exists():
            return {'error': 'Record not found'}
        return {
            'id': record.id,
            'name': record.name,
            'title': record.title,
            'create_date': str(record.create_date),
        }

    @http.route('/test/update', type='json', auth='user', csrf=False)
    def test_update(self, id, **kwargs):
        if not id:
            return {"error": "Missing id"}

        # lấy record với id truyền vào để update
        record = request.env['test.model'].browse(id)

        # kiểm tra nếu như mà không có quyền thì thông báo lỗi
        if not record.exists():
            return {"error": "Record not found"}

        # update dòng vừa lấy ra
        # Lấy các field từ kwargs
        name = kwargs.get('name')
        title = kwargs.get('title')
        update_values = {}

        if name is not None:
            update_values['name'] = name

        if title is not None:
            update_values['title'] = title
        
        # update kiểm tra xem có trường nào cần update không
        if update_values:
            # thực hiện update vào cơ sở dữ liệu
            record.write(update_values)
            return {"status": "success"}
        else:
            return {"status": "no_update", "message": "No fields to update"}

