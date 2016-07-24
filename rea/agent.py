from openerp import fields, models


class Agent(models.Model):
    """ Person or organization having control over economic Resources
    and participating in economic Events
    """
    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.agent.type',
        string="Type")


class AgentType(models.Model):
    """ Abstract definition of actual Agents
    """
    name = fields.Char(
        string="name",
        required=True,
        index=True)
