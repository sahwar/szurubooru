import sqlalchemy
from szurubooru import db, errors
from szurubooru.func import util
from szurubooru.search import criteria


def wildcard_transformer(value):
    return (value
        .replace('%', r'\%')
        .replace('_', r'\_')
        .replace('*', '%'))


def apply_num_criterion_to_column(column, criterion):
    '''
    Decorate SQLAlchemy filter on given column using supplied criterion.
    '''
    try:
        if isinstance(criterion, criteria.PlainCriterion):
            expr = column == int(criterion.value)
        elif isinstance(criterion, criteria.ArrayCriterion):
            expr = column.in_(int(value) for value in criterion.values)
        elif isinstance(criterion, criteria.RangedCriterion):
            assert criterion.min_value != '' \
                or criterion.max_value != ''
            if criterion.min_value != '' and criterion.max_value != '':
                expr = column.between(
                    int(criterion.min_value), int(criterion.max_value))
            elif criterion.min_value != '':
                expr = column >= int(criterion.min_value)
            elif criterion.max_value != '':
                expr = column <= int(criterion.max_value)
        else:
            assert False
    except ValueError:
        raise errors.SearchError(
            'Criterion value %r must be a number.' % (criterion,))
    return expr


def create_num_filter(column):
    def wrapper(query, criterion, negated):
        expr = apply_num_criterion_to_column(
            column, criterion)
        if negated:
            expr = ~expr
        return query.filter(expr)
    return wrapper


def apply_str_criterion_to_column(
        column, criterion, transformer=wildcard_transformer):
    '''
    Decorate SQLAlchemy filter on given column using supplied criterion.
    '''
    if isinstance(criterion, criteria.PlainCriterion):
        expr = column.ilike(transformer(criterion.value))
    elif isinstance(criterion, criteria.ArrayCriterion):
        expr = sqlalchemy.sql.false()
        for value in criterion.values:
            expr = expr | column.ilike(transformer(value))
    elif isinstance(criterion, criteria.RangedCriterion):
        expr = column.ilike(transformer(criterion.original_text))
    else:
        assert False
    return expr


def create_str_filter(column, transformer=wildcard_transformer):
    def wrapper(query, criterion, negated):
        expr = apply_str_criterion_to_column(
            column, criterion, transformer)
        if negated:
            expr = ~expr
        return query.filter(expr)
    return wrapper


def apply_date_criterion_to_column(column, criterion):
    '''
    Decorate SQLAlchemy filter on given column using supplied criterion.
    Parse the datetime inside the criterion.
    '''
    if isinstance(criterion, criteria.PlainCriterion):
        min_date, max_date = util.parse_time_range(criterion.value)
        expr = column.between(min_date, max_date)
    elif isinstance(criterion, criteria.ArrayCriterion):
        expr = sqlalchemy.sql.false()
        for value in criterion.values:
            min_date, max_date = util.parse_time_range(value)
            expr = expr | column.between(min_date, max_date)
    elif isinstance(criterion, criteria.RangedCriterion):
        assert criterion.min_value or criterion.max_value
        if criterion.min_value and criterion.max_value:
            min_date = util.parse_time_range(criterion.min_value)[0]
            max_date = util.parse_time_range(criterion.max_value)[1]
            expr = column.between(min_date, max_date)
        elif criterion.min_value:
            min_date = util.parse_time_range(criterion.min_value)[0]
            expr = column >= min_date
        elif criterion.max_value:
            max_date = util.parse_time_range(criterion.max_value)[1]
            expr = column <= max_date
    else:
        assert False
    return expr


def create_date_filter(column):
    def wrapper(query, criterion, negated):
        expr = apply_date_criterion_to_column(
            column, criterion)
        if negated:
            expr = ~expr
        return query.filter(expr)
    return wrapper


def create_subquery_filter(
        left_id_column,
        right_id_column,
        filter_column,
        filter_factory,
        subquery_decorator=None):
    filter_func = filter_factory(filter_column)

    def wrapper(query, criterion, negated):
        subquery = db.session.query(right_id_column.label('foreign_id'))
        if subquery_decorator:
            subquery = subquery_decorator(subquery)
        subquery = subquery.options(sqlalchemy.orm.lazyload('*'))
        subquery = filter_func(subquery, criterion, False)
        subquery = subquery.subquery('t')
        expression = left_id_column.in_(subquery)
        if negated:
            expression = ~expression
        return query.filter(expression)

    return wrapper
