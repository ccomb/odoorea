from . import model  # noqa
from odoo import tools
tools.generate_views_for(model, 'lifecycle', 'identifier', 'property')