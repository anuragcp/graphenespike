#!/usr/bin/env python

import routes
import cql
import models

def main():
    sess = cql.session()
    models.init(sess)
    routes.app.run(use_reloader=True)

if "__main__" == __name__:
    main()
