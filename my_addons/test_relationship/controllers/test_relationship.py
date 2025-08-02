from odoo import http
from odoo.http import request

class TestRelationshipController(http.Controller):

    @http.route('/test_relationship/list', type='json', auth='user')
    def test_relationship_list(self, name=None, page=1, page_size=10):
        domain = []
        if name:
            domain.append(('name', 'ilike', name))

        # Tính offset và limit
        try:
            page = int(page)
            page_size = int(page_size)
        except Exception:
            page, page_size = 1, 10

        offset = (page - 1) * page_size
        total_count = request.env['test_relationship.model'].search_count(domain)
        
        records = request.env['test_relationship.model'].search(domain, offset=offset, limit=page_size)

        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "results": [
                {
                    'id': r.id,
                    'name': r.name,
                }
                for r in records
            ]
        }

    @http.route('/test_relationship/create', type='json', auth='user')
    def test_relationship_create(self, **kwargs):
        name = kwargs.get('name')
        # nếu bắt buộc có name
        if not name:
            return {'error': 'Missing name'}
        
        # Bỏ name và title lấy được vào values: values này dùng để tạo đối tượng
        values = {
            'name': name,
        }

        # record này là đối tượng lấy từ hàm create bên dưới
        # hàm create(values): create nhận values đã tạo bên trên để tạo đối tượng phù hợp với model
        # env['test.model']: cái này là để biết thực hiện create trên model nào
        # test.model chính là cái _name bình đặt ở bên models/test.py
        record = request.env['test_relationship.model'].create(values)
        
        # Trả về đối tượng vừa được tạo
        return {
            'id': record.id,
            'name': record.name,
        }
    
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
            'image': record.image,
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
        image = kwargs.get('image')
        update_values = {}

        if name is not None:
            update_values['name'] = name

        if title is not None:
            update_values['title'] = title
        
        if image is not None:
            update_values['image'] = image
        
        # update kiểm tra xem có trường nào cần update không
        if update_values:
            # thực hiện update vào cơ sở dữ liệu
            record.write(update_values)
            return {"status": "success"}
        else:
            return {"status": "no_update", "message": "No fields to update"}

