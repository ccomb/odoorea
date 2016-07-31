from openerp import fields, models


class Agent(models.Model):
    """ Person or organization having control over economic Resources
    and participating in economic Events
    """
    _name = 'rea.agent'
    _description = 'Agent'

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.agent.type',
        string="Type")
    groups = fields.Many2many(
        'rea.agent.group',
        string="Groups")


class AgentType(models.Model):
    """ Abstract definition of actual Agents
    """
    _name = 'rea.agent.type'
    _description = 'Agent Type'

    name = fields.Char(
        string="name",
        required=True,
        index=True)


class AgentGroup(models.Model):
    """ Group of agents
    """
    _name = 'rea.agent.group'
    _description = "Agent Group"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    groups = fields.Many2one(
        'rea.agent.group',
        string="Group")
