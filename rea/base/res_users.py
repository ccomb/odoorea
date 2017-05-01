from openerp import fields, models


class Users(models.Model):
    """Link a res.users to its corresponding Agent
    """
    _inherit = 'res.users'
    agent_id = fields.Many2one('rea.agent')


class Agent(models.Model):
    """ Link an agent to its corresponding users
    """
    _inherit = 'rea.agent'
    user_ids = fields.One2many(
        'res.users',
        inverse_name='agent_id')
