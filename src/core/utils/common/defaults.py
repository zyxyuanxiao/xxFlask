#!/usr/bin/python
# -*- coding: utf-8 -*-

import utility as u

defaults = [
    ['SCRIPT_APP_VERSION', '1.0'],
    ['SCRIPT_APP_REVISION', u.get_env('SVN_REVISION', 0)],
    ['BUILD_RES_STRATEGY', u.get_env('BUILD_RES_STRATEGY', 'SINGLE')],
]
