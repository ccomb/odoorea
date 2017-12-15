from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Contract(models.Model):
    """ Set of commitments and terms forming clauses
    """
    _name = 'rea.contract'
    _description = "REA Contract"
    _inherit = [
        'rea.identifiable.entity',
        'rea.lifecycleable.entity']

    def _default_parties(self):
        """the relative company depends on the user
        """
        if self.env.user.company:
            return [(6, 0, [self.env.user.company.id])]
        return []

    @api.onchange('parties')  # TODO add a _constraint
    def _change_parties(self):
        for c in self:
            parties = c.parties
            if len(parties) > c.type.max_parties > 0:
                c.parties = parties[:c.type.max_parties-1]
                raise ValidationError(
                    u"This contract type cannot have more than {} parties"
                    .format(c.type.max_parties))

    name = fields.Char(
        string="name",
        required=True,
        default=lambda self: _('New'),
        index=True)
    type = fields.Many2one(
        'rea.contract.type',
        required=True,
        string="Type")
    groups = fields.Many2many(
        'rea.commitment.group',
        string="Groups")
    parties = fields.Many2many(
        'rea.agent',
        string="Agents",
        default=_default_parties,
        help="Agents involved in this contract.")
    clauses = fields.One2many(
        'rea.commitment',
        'contract',
        copy=True,
        string="Commitments",
        help="The commitments of the contract")
    terms = fields.One2many(
        'rea.contract.term',
        'contract',
        string="Clauses",
        help=("Clauses contain the text of the contract and allow to generate"
              " commitments, possibly depending on other commitments"))
    start = fields.Date(
        string="Starts on")
    end = fields.Date(
        string="Expires on")
    signed = fields.Date(
        string="Signature date")
    validity = fields.Date(
        string="Valid until")

    def confirm(self):
        # TODO make it configurable in the lifecycle
        for c in self:
            if c.state == 'draft':
                c.write({'state': 'confirmed'})
                c.clauses.confirm()
            else:
                raise ValidationError(
                    u"Contract {} cannot be confirmed".format(c.name))

    def cancel(self):
        for c in self:
            if c.state == 'confirmed':
                c.write({'state': 'canceled'})
                c.clauses.cancel()
            else:
                raise ValidationError(
                    u"Contract {} cannot be canceled".format(c.name))

    def unlink(self):
        for c in self:
            if (not c.step or c.step.state == 'draft'
                    or c.step.state == 'canceled' and c.type.allow_delete):
                super(Contract, c).unlink()
            else:
                raise ValidationError(
                    u"Contract {} cannot be deleted".format(c.name))


class ContractType(models.Model):
    """ Abstract definition of actual contracts
    """
    _name = 'rea.contract.type'
    _description = "Contract Type"
    _inherit = ['rea.identifiable.type',
                'rea.lifecycleable.type',
                'rea.identifiable.entity']

    name = fields.Char(
        string="Contract Type",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.contract.type',
        string="Type")
    subtypes = fields.One2many(
        'rea.contract.type',
        'type',
        copy=True,
        string="Sub-types")
    party_types = fields.Many2many(
        'rea.agent.type',
        string="Agent Types")
    max_parties = fields.Integer(
        "Max nb of parties")
    commitment_types = fields.Many2many(
        'rea.commitment.type',
        string="Commitment Types")
    allow_delete = fields.Boolean(
        u"Allow to delete",
        help=u"Allow to delete draft or canceled contracts")


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


class ContractTerm(models.Model):
    """ What happens if clauses are not fullfilled
    (generate additional commitments)
    """
    _name = 'rea.contract.term'
    _description = "REA Contract term"

    name = fields.Char(
        string="name",
        required=True)
    contract = fields.Many2one(
        'rea.contract',
        string="Contract")


# TODO ClauseType ??
