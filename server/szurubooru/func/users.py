import datetime
import re
from sqlalchemy import func
from szurubooru import config, db, errors
from szurubooru.func import auth, util, files, images


class UserNotFoundError(errors.NotFoundError):
    pass


class UserAlreadyExistsError(errors.ValidationError):
    pass


class InvalidUserNameError(errors.ValidationError):
    pass


class InvalidEmailError(errors.ValidationError):
    pass


class InvalidPasswordError(errors.ValidationError):
    pass


class InvalidRankError(errors.ValidationError):
    pass


class InvalidAvatarError(errors.ValidationError):
    pass


def get_avatar_path(user_name):
    return 'avatars/' + user_name.lower() + '.png'


def get_avatar_url(user):
    assert user
    if user.avatar_style == user.AVATAR_GRAVATAR:
        assert user.email or user.name
        return 'https://gravatar.com/avatar/%s?d=retro&s=%d' % (
            util.get_md5((user.email or user.name).lower()),
            config.config['thumbnails']['avatar_width'])
    else:
        assert user.name
        return '%s/avatars/%s.png' % (
            config.config['data_url'].rstrip('/'), user.name.lower())


def get_email(user, auth_user, force_show_email):
    assert user
    assert auth_user
    if not force_show_email \
            and auth_user.user_id != user.user_id \
            and not auth.has_privilege(auth_user, 'users:edit:any:email'):
        return False
    return user.email


def get_liked_post_count(user, auth_user):
    assert user
    assert auth_user
    if auth_user.user_id != user.user_id:
        return False
    return user.liked_post_count


def get_disliked_post_count(user, auth_user):
    assert user
    assert auth_user
    if auth_user.user_id != user.user_id:
        return False
    return user.disliked_post_count


def serialize_user(user, auth_user, options=None, force_show_email=False):
    return util.serialize_entity(
        user,
        {
            'name': lambda: user.name,
            'creationTime': lambda: user.creation_time,
            'lastLoginTime': lambda: user.last_login_time,
            'version': lambda: user.version,
            'rank': lambda: user.rank,
            'avatarStyle': lambda: user.avatar_style,
            'avatarUrl': lambda: get_avatar_url(user),
            'commentCount': lambda: user.comment_count,
            'uploadedPostCount': lambda: user.post_count,
            'favoritePostCount': lambda: user.favorite_post_count,
            'likedPostCount':
                lambda: get_liked_post_count(user, auth_user),
            'dislikedPostCount':
                lambda: get_disliked_post_count(user, auth_user),
            'email':
                lambda: get_email(user, auth_user, force_show_email),
        },
        options)


def serialize_micro_user(user, auth_user):
    return serialize_user(
        user,
        auth_user=auth_user,
        options=['name', 'avatarUrl'])


def get_user_count():
    return db.session.query(db.User).count()


def try_get_user_by_name(name):
    return db.session \
        .query(db.User) \
        .filter(func.lower(db.User.name) == func.lower(name)) \
        .one_or_none()


def get_user_by_name(name):
    user = try_get_user_by_name(name)
    if not user:
        raise UserNotFoundError('User %r not found.' % name)
    return user


def try_get_user_by_name_or_email(name_or_email):
    return (db.session
        .query(db.User)
        .filter(
            (func.lower(db.User.name) == func.lower(name_or_email)) |
            (func.lower(db.User.email) == func.lower(name_or_email)))
        .one_or_none())


def get_user_by_name_or_email(name_or_email):
    user = try_get_user_by_name_or_email(name_or_email)
    if not user:
        raise UserNotFoundError('User %r not found.' % name_or_email)
    return user


def create_user(name, password, email):
    user = db.User()
    update_user_name(user, name)
    update_user_password(user, password)
    update_user_email(user, email)
    if get_user_count() > 0:
        user.rank = util.flip(auth.RANK_MAP)[config.config['default_rank']]
    else:
        user.rank = db.User.RANK_ADMINISTRATOR
    user.creation_time = datetime.datetime.utcnow()
    user.avatar_style = db.User.AVATAR_GRAVATAR
    return user


def update_user_name(user, name):
    assert user
    if not name:
        raise InvalidUserNameError('Name cannot be empty.')
    if util.value_exceeds_column_size(name, db.User.name):
        raise InvalidUserNameError('User name is too long.')
    name = name.strip()
    name_regex = config.config['user_name_regex']
    if not re.match(name_regex, name):
        raise InvalidUserNameError(
            'User name %r must satisfy regex %r.' % (name, name_regex))
    other_user = try_get_user_by_name(name)
    if other_user and other_user.user_id != user.user_id:
        raise UserAlreadyExistsError('User %r already exists.' % name)
    if user.name and files.has(get_avatar_path(user.name)):
        files.move(get_avatar_path(user.name), get_avatar_path(name))
    user.name = name


def update_user_password(user, password):
    assert user
    if not password:
        raise InvalidPasswordError('Password cannot be empty.')
    password_regex = config.config['password_regex']
    if not re.match(password_regex, password):
        raise InvalidPasswordError(
            'Password must satisfy regex %r.' % password_regex)
    user.password_salt = auth.create_password()
    user.password_hash = auth.get_password_hash(user.password_salt, password)


def update_user_email(user, email):
    assert user
    if email:
        email = email.strip()
    if not email:
        email = None
    if email and util.value_exceeds_column_size(email, db.User.email):
        raise InvalidEmailError('Email is too long.')
    if not util.is_valid_email(email):
        raise InvalidEmailError('E-mail is invalid.')
    user.email = email


def update_user_rank(user, rank, auth_user):
    assert user
    if not rank:
        raise InvalidRankError('Rank cannot be empty.')
    rank = util.flip(auth.RANK_MAP).get(rank.strip(), None)
    all_ranks = list(auth.RANK_MAP.values())
    if not rank:
        raise InvalidRankError(
            'Rank can be either of %r.' % all_ranks)
    if rank in (db.User.RANK_ANONYMOUS, db.User.RANK_NOBODY):
        raise InvalidRankError('Rank %r cannot be used.' % auth.RANK_MAP[rank])
    if all_ranks.index(auth_user.rank) \
            < all_ranks.index(rank) and get_user_count() > 0:
        raise errors.AuthError('Trying to set higher rank than your own.')
    user.rank = rank


def update_user_avatar(user, avatar_style, avatar_content=None):
    assert user
    if avatar_style == 'gravatar':
        user.avatar_style = user.AVATAR_GRAVATAR
    elif avatar_style == 'manual':
        user.avatar_style = user.AVATAR_MANUAL
        avatar_path = 'avatars/' + user.name.lower() + '.png'
        if not avatar_content:
            if files.has(avatar_path):
                return
            raise InvalidAvatarError('Avatar content missing.')
        image = images.Image(avatar_content)
        image.resize_fill(
            int(config.config['thumbnails']['avatar_width']),
            int(config.config['thumbnails']['avatar_height']))
        files.save(avatar_path, image.to_png())
    else:
        raise InvalidAvatarError(
            'Avatar style %r is invalid. Valid avatar styles: %r.' % (
                avatar_style, ['gravatar', 'manual']))


def bump_user_login_time(user):
    assert user
    user.last_login_time = datetime.datetime.utcnow()


def reset_user_password(user):
    assert user
    password = auth.create_password()
    user.password_salt = auth.create_password()
    user.password_hash = auth.get_password_hash(user.password_salt, password)
    return password
