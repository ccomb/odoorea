from openerp import fields, models


class Contract(models.Model):
    """ Set of Clauses applying to Agents and generating Commitments
    """
    _name = 'rea.contract'
    _description = "REA Contract"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.contract.type',
        string="Type")
    agents = fields.Many2many(
        'rea.agent',
        string="Agents",
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
        string="Signature date")
    end = fields.Date(
        string="Expiration date")


class ContractType(models.Model):
    """ Abstract definition of actual contracts"""
    _name = 'rea.contract.type'
    _description = "Contract Type"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    agent_types = fields.Many2many(
        'rea.agent.type',
        string="Agent Types")
    commitment_types = fields.Many2many(
        'rea.commitment.type',
        string="Commitment Types")


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
