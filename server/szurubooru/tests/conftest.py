# pylint: disable=redefined-outer-name
import contextlib
import os
import random
import string
from datetime import datetime
import pytest
import freezegun
import sqlalchemy
from szurubooru import config, db, rest


class QueryCounter(object):
    def __init__(self):
        self._statements = []

    def __enter__(self):
        self._statements = []

    def __exit__(self, *args, **kwargs):
        self._statements = []

    def create_before_cursor_execute(self):
        def before_cursor_execute(
                _conn, _cursor, statement, _params, _context, _executemany):
            self._statements.append(statement)
        return before_cursor_execute

    @property
    def statements(self):
        return self._statements


if not config.config['test_database']:
    raise RuntimeError('Test database not configured.')

_query_counter = QueryCounter()
_engine = sqlalchemy.create_engine(config.config['test_database'])
db.Base.metadata.drop_all(bind=_engine)
db.Base.metadata.create_all(bind=_engine)
sqlalchemy.event.listen(
    _engine,
    'before_cursor_execute',
    _query_counter.create_before_cursor_execute())


def get_unique_name():
    alphabet = string.ascii_letters + string.digits
    return ''.join(random.choice(alphabet) for _ in range(8))


@pytest.fixture
def fake_datetime():
    @contextlib.contextmanager
    def injector(now):
        freezer = freezegun.freeze_time(now)
        freezer.start()
        yield
        freezer.stop()
    return injector


@pytest.fixture()
def query_counter():
    return _query_counter


@pytest.fixture
def query_logger():
    if pytest.config.option.verbose > 0:
        import logging
        import coloredlogs
        coloredlogs.install(
            fmt='[%(asctime)-15s] %(name)s %(message)s', isatty=True)
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


@pytest.yield_fixture(scope='function', autouse=True)
def session(query_logger):  # pylint: disable=unused-argument
    db.sessionmaker = sqlalchemy.orm.sessionmaker(
        bind=_engine, autoflush=False)
    db.session = sqlalchemy.orm.scoped_session(db.sessionmaker)
    try:
        yield db.session
    finally:
        db.session.remove()
        for table in reversed(db.Base.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()


@pytest.fixture
def context_factory(session):
    def factory(params=None, files=None, user=None):
        ctx = rest.Context(
            method=None,
            url=None,
            headers={},
            params=params or {},
            files=files or {})
        ctx.session = session
        ctx.user = user or db.User()
        return ctx
    return factory


@pytest.fixture
def config_injector():
    def injector(new_config_content):
        config.config = new_config_content
    return injector


@pytest.fixture
def user_factory():
    def factory(name=None, rank=db.User.RANK_REGULAR, email='dummy'):
        user = db.User()
        user.name = name or get_unique_name()
        user.password_salt = 'dummy'
        user.password_hash = 'dummy'
        user.email = email
        user.rank = rank
        user.creation_time = datetime(1997, 1, 1)
        user.avatar_style = db.User.AVATAR_GRAVATAR
        return user
    return factory


@pytest.fixture
def tag_category_factory():
    def factory(name=None, color='dummy', default=False):
        category = db.TagCategory()
        category.name = name or get_unique_name()
        category.color = color
        category.default = default
        return category
    return factory


@pytest.fixture
def tag_factory():
    def factory(names=None, category=None):
        if not category:
            category = db.TagCategory(get_unique_name())
            db.session.add(category)
        tag = db.Tag()
        tag.names = []
        for i, name in enumerate(names or [get_unique_name()]):
            tag.names.append(db.TagName(name, i))
        tag.category = category
        tag.creation_time = datetime(1996, 1, 1)
        return tag
    return factory


@pytest.fixture
def post_factory():
    # pylint: disable=invalid-name
    def factory(
            id=None,
            safety=db.Post.SAFETY_SAFE,
            type=db.Post.TYPE_IMAGE,
            checksum='...'):
        post = db.Post()
        post.post_id = id
        post.safety = safety
        post.type = type
        post.checksum = checksum
        post.flags = []
        post.mime_type = 'application/octet-stream'
        post.creation_time = datetime(1996, 1, 1)
        return post
    return factory


@pytest.fixture
def comment_factory(user_factory, post_factory):
    def factory(user=None, post=None, text='dummy', time=None):
        if not user:
            user = user_factory()
            db.session.add(user)
        if not post:
            post = post_factory()
            db.session.add(post)
        comment = db.Comment()
        comment.user = user
        comment.post = post
        comment.text = text
        comment.creation_time = time or datetime(1996, 1, 1)
        return comment
    return factory


@pytest.fixture
def read_asset():
    def get(path):
        path = os.path.join(os.path.dirname(__file__), 'assets', path)
        with open(path, 'rb') as handle:
            return handle.read()
    return get
