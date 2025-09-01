from odoo.exceptions import AccessError


def check_employee_permission(env, collection_unit_id, action_code):
    """
    Kiểm tra quyền của employee theo đơn vị thu gom + action.
    
    :param env: self.env
    :param collection_unit_id: id của env.collectionunit cần check
    :param action_code: mã quyền cần check (edit_customer, add_customer, ...)
    :raise AccessError: nếu không có quyền
    """
    user = env.user

    # Nếu không phải employee thì bỏ qua check (admin/manager không cần)
    if not user.has_group('environment.group_env_employee'):
        return True

    # Lấy tất cả group mà user thuộc vào
    groups = env['env.collectionunitgroup'].search([
        ('member_ids', 'in', [user.id]),
        ('collection_unit_id', '=', collection_unit_id),
    ])

    # Kiểm tra quyền trong nhóm
    has_permission = any(
        any(action.code == action_code for action in group.action_ids)
        for group in groups
    )

    if not has_permission:
        raise AccessError(
            "Bạn không có quyền '%s' trong đơn vị thu gom này." % action_code
        )

    return True
