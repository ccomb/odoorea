from . import identifier  # noqa
from . import lifecycle  # noqa
from . import observable  # noqa
from . import property  # noqa
from subprocess import call

from odoo import tools
from os.path import join, dirname, exists


def generate_views(_file_, name, inherits):
    """ create inherited views to add behaviours to models
    """
    # dynamically generated view for behaviours
    for inherit in inherits:
        _, kind, behav = inherit.split('.')
        tmpl = join(dirname(__file__), behav, '%s.%s.tmpl.xml' % (behav, kind))
        target = join(dirname(_file_), 'behaviours.xml')
        content = (open(tmpl).read()
                   .replace('${xmlid}', name.replace('.', '_'))
                   .replace('${object}', name))
        head = ('<?xml version="1.0" encoding="utf-8"?>\n'
                '<!-- GENERATED FILE DO NOT EDIT -->\n<odoo>\n')
        tail = '</odoo>'
        if not exists(target):
            with open(target, 'w') as t:
                t.write(head + tail)
        with open(target) as t:
            old = t.readlines()[3:-1]
        with open(target, 'w') as t:
            t.write(head + ''.join(old) + '\n' + content + tail)


tools.generate_views = generate_views

# delete generated file just before recreating them in upcoming class defs
reafolder = dirname(dirname(__file__))
call('find "%s" -name behaviours.xml -delete' % reafolder, shell=True)
