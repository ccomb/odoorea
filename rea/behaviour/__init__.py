from . import identifier  # noqa
from . import lifecycle  # noqa
from . import observable  # noqa
from . import property  # noqa

from odoo import tools
from os.path import join, dirname


def generate_views_for(model, *behaviours):
    """ create inherited views to add behaviours to models
    """
    entity = model.__name__.split('.')[-2]
    # dynamically generated view for behaviours
    for behav in behaviours:
        source = join(dirname(__file__), behav, behav + '.tmpl.xml')
        target = join(dirname(model.__file__), behav + '.xml')
        content = (open(source).read()
                   .replace('${object}', entity)
                   .replace('${Object}', entity.capitalize()))
        open(target, 'w').write(content)


tools.generate_views_for = generate_views_for
