from szurubooru import search
from szurubooru.rest import routes
from szurubooru.func import auth, users, util, versions


_search_executor = search.Executor(search.configs.UserSearchConfig())


def _serialize(ctx, user, **kwargs):
    return users.serialize_user(
        user,
        ctx.user,
        options=util.get_serialization_options(ctx),
        **kwargs)


@routes.get('/users/?')
def get_users(ctx, _params=None):
    auth.verify_privilege(ctx.user, 'users:list')
    return _search_executor.execute_and_serialize(
        ctx, lambda user: _serialize(ctx, user))


@routes.post('/users/?')
def create_user(ctx, _params=None):
    auth.verify_privilege(ctx.user, 'users:create')
    name = ctx.get_param_as_string('name', required=True)
    password = ctx.get_param_as_string('password', required=True)
    email = ctx.get_param_as_string('email', required=False, default='')
    user = users.create_user(name, password, email)
    if ctx.has_param('rank'):
        users.update_user_rank(
            user, ctx.get_param_as_string('rank'), ctx.user)
    if ctx.has_param('avatarStyle'):
        users.update_user_avatar(
            user,
            ctx.get_param_as_string('avatarStyle'),
            ctx.get_file('avatar'))
    ctx.session.add(user)
    ctx.session.commit()
    return _serialize(ctx, user, force_show_email=True)


@routes.get('/user/(?P<user_name>[^/]+)/?')
def get_user(ctx, params):
    user = users.get_user_by_name(params['user_name'])
    if ctx.user.user_id != user.user_id:
        auth.verify_privilege(ctx.user, 'users:view')
    return _serialize(ctx, user)


@routes.put('/user/(?P<user_name>[^/]+)/?')
def update_user(ctx, params):
    user = users.get_user_by_name(params['user_name'])
    versions.verify_version(user, ctx)
    versions.bump_version(user)
    infix = 'self' if ctx.user.user_id == user.user_id else 'any'
    if ctx.has_param('name'):
        auth.verify_privilege(ctx.user, 'users:edit:%s:name' % infix)
        users.update_user_name(user, ctx.get_param_as_string('name'))
    if ctx.has_param('password'):
        auth.verify_privilege(ctx.user, 'users:edit:%s:pass' % infix)
        users.update_user_password(
            user, ctx.get_param_as_string('password'))
    if ctx.has_param('email'):
        auth.verify_privilege(ctx.user, 'users:edit:%s:email' % infix)
        users.update_user_email(user, ctx.get_param_as_string('email'))
    if ctx.has_param('rank'):
        auth.verify_privilege(ctx.user, 'users:edit:%s:rank' % infix)
        users.update_user_rank(
            user, ctx.get_param_as_string('rank'), ctx.user)
    if ctx.has_param('avatarStyle'):
        auth.verify_privilege(ctx.user, 'users:edit:%s:avatar' % infix)
        users.update_user_avatar(
            user,
            ctx.get_param_as_string('avatarStyle'),
            ctx.get_file('avatar'))
    ctx.session.commit()
    return _serialize(ctx, user)


@routes.delete('/user/(?P<user_name>[^/]+)/?')
def delete_user(ctx, params):
    user = users.get_user_by_name(params['user_name'])
    versions.verify_version(user, ctx)
    infix = 'self' if ctx.user.user_id == user.user_id else 'any'
    auth.verify_privilege(ctx.user, 'users:delete:%s' % infix)
    ctx.session.delete(user)
    ctx.session.commit()
    return {}
