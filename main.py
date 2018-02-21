#!/usr/bin/env python

import cql
import flask_graphql as graphql
import flask_opentracing as ot
import jaeger_client as jaeger
import graphql.type.definition as definition
import models
import routes
import schema

def initialize_tracer():
    """
    initialize_tracer
    """
    config = jaeger.Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
        },
        service_name='swapi',
    )
    return config.initialize_tracer()

tracer = ot.FlaskTracer(initialize_tracer, True, routes.app)

def operation_name(parent_type, field_name):
    if parent_type is None:
        return field_name

    return "{parent_type}.{field_name}".format(
                parent_type=parent_type,
                field_name=field_name,
            )

def tracer_middleware(next, root, info, **args):
    """
    tracer_middleware adds trace spans to each field resolver call.
    """
    parent_type = None
    if root and hasattr(root, '_meta'):
        parent_type = root._meta.name

    if isinstance(info.return_type, definition.GraphQLScalarType):
        return_value = next(root, info, **args)
    else:
        parent_span = tracer.get_span()
        child_span = tracer._tracer.start_span(
                operation_name(parent_type, info.field_name),
                child_of=parent_span,
            )
        return_value = next(root, info, **args)
        child_span.finish()

    return return_value

def main():
    print("listening :5000 ...")
    sess = cql.session()
    models.init(sess)
    view = graphql.GraphQLView.as_view(
        'graphql',
        schema=schema.schema,
        middleware=[tracer_middleware],
        graphiql=True,
        graphiql_template=schema.HTML)
    routes.app.add_url_rule("/graphql", view_func=view)
    routes.app.run(use_reloader=True)

if "__main__" == __name__:
    main()
