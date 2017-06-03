from openerp import fields, models


class Users(models.Model):
    """Link a res.users to its corresponding Agent
    and 
    """
    _inherit = 'res.users'
    agent = fields.Many2one('rea.agent')
    company = fields.Many2one('rea.agent')


class Agent(models.Model):
    """ Link an agent to its corresponding users
    """
    _inherit = 'rea.agent'
    users = fields.One2many(
        'res.users',
        inverse_name='agent')
