from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Contract(models.Model):
    """ Set of Clauses applying to Agents and generating Commitments
    """
    _name = 'rea.contract'
    _description = "REA Contract"
    _inherit = ['rea.ident.sequence']

    def _default_agents(self):
        """the relative company depends on the user
        """
        groups = self.env.user.agent.groups
        for group in groups:  # FIXME coz it returns the 1st group with agent
            if group.agent.id:
                return [(6, 0, [group.agent.id])]
        return []

    @api.onchange('agents')  # TODO add a _constraint
    def _change_agents(self):
        for c in self:
            agents = c.agents
            if len(agents) > c.type.max_agents > 0:
                c.agents = agents[:c.type.max_agents-1]
                raise UserError(
                    u"This contract type cannot have more than {} agents"
                    .format(c.type.max_agents))

    name = fields.Char(
        string="name",
        required=True,
        default=lambda self: _('New'),
        index=True)
    type = fields.Many2one(
        'rea.contract.type',
        string="Type")
    groups = fields.Many2many(
        'rea.commitment.group',
        string="Groups")
    agents = fields.Many2many(
        'rea.agent',
        string="Agents",
        default=_default_agents,
        help="Agents involved in this contract.")
    clauses = fields.One2many(
        'rea.contract.clause',
        'contract',
        string="Clauses",
        help=("Clauses contain the text of the contract and allow to generate"
              " commitments, possibly depending on other commitments"))
    commitments = fields.One2many(
        'rea.commitment',
        'contract',
        string="Commitments",
        help="The commitments of the contract")
    start = fields.Date(
        string="Starts on")
    end = fields.Date(
        string="Expires on")
    signed = fields.Date(
        string="Signature date")
    validity = fields.Date(
        string="Valid until")


class ContractType(models.Model):
    """ Abstract definition of actual contracts
    """
    _name = 'rea.contract.type'
    _description = "Contract Type"
    _inherit = ['rea.ident.sequence.store']

    name = fields.Char(
        string="Contract Type",
        required=True,
        index=True)
    agent_types = fields.Many2many(
        'rea.agent.type',
        string="Agent Types")
    max_agents = fields.Integer(
        "Max nb of agents")
    commitment_types = fields.Many2many(
        'rea.commitment.type',
        string="Commitment Types")


class ContractGroup(models.Model):
    """ Group of contracts
    """
    _name = 'rea.contract.group'
    _description = "Contract Group"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    groups = fields.Many2one(
        'rea.contract.group',
        string="Group")


class Clause(models.Model):
    """ Piece of contract generating commitments
    """
    _name = 'rea.contract.clause'
    _description = "REA Contract clause"

    name = fields.Char(
        string="name",
        required=True)
    contract = fields.Many2one(
        'rea.contract',
        string="Contract")
    conditions = fields.Selection([
        ('foobar', 'Foobar'),
    ])


# TODO ClauseType ??
