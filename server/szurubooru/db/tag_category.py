from sqlalchemy import Column, Integer, Unicode, Boolean, table
from sqlalchemy.orm import column_property
from sqlalchemy.sql.expression import func, select
from szurubooru.db.base import Base
from szurubooru.db.tag import Tag


class TagCategory(Base):
    __tablename__ = 'tag_category'

    tag_category_id = Column('id', Integer, primary_key=True)
    version = Column('version', Integer, default=1, nullable=False)
    name = Column('name', Unicode(32), nullable=False)
    color = Column('color', Unicode(32), nullable=False, default='#000000')
    default = Column('default', Boolean, nullable=False, default=False)

    def __init__(self, name=None):
        self.name = name

    tag_count = column_property(
        select([func.count('Tag.tag_id')])
        .where(Tag.category_id == tag_category_id)
        .correlate_except(table('Tag')))

    __mapper_args__ = {
        'version_id_col': version,
        'version_id_generator': False,
    }
