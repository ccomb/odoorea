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
    _parent_name = 'type'

    type = fields.Many2one(
        'rea.agent.type',
        string="Type")
    structural = fields.Boolean(
        'Structural type?',
        help="Hide in operational choices?")
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
    groups = fields.Many2many(
        'rea.agent.group',
        'rea_agent_group_group',
        'group1_id', 'group2_id',
        help=u"Groups this group is part of",
        string=u"Groups")
    agent = fields.Many2one(
        'rea.agent',
        "Related Agent",
        help=u"Agent corresponding to this group, if any")
    agents = fields.Many2many(
        'rea.agent',
        string="Members")
