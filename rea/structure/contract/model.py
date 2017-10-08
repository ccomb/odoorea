from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Contract(models.Model):
    """ Set of Clauses applying to Agents and generating Commitments
    """
    _name = 'rea.contract'
    _description = "REA Contract"
    _inherit = ['rea.ident.sequence',
                'rea.behaviour.lifecycle']
    _behaviours = {'step': 'rea.contract.step'}

    def _default_parties(self):
        """the relative company depends on the user
        """
        return [(6, 0, [self.env.user.company.id])]

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
        'rea.commitment',  # rea.contract.clause?
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
            if (c.state == 'draft'
                    or c.state == 'canceled' and c.type.allow_delete):
                super(Contract, c).unlink()
            else:
                raise ValidationError(
                    u"Contract {} cannot be deleted".format(c.name))


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
    conditions = fields.Selection([
        ('foobar', 'Foobar'),
    ])


# TODO ClauseType ??


class ContractStep(models.Model):
    """State of contracts
    """
    # TODO: make it dynamically optional
    _inherit = 'rea.lifecycle.step'
    _name = 'rea.contract.step'
    type = fields.Many2one(
        'rea.contract.type',
        'Contract type',
        required=True,
        ondelete='cascade')


class ContractWithStep(models.Model):
    _inherit = 'rea.contract'

    @api.model
    def create(self, values):
        """select the default step if parent is selected lately
        """
        if not values.get('step'):
            type = self.type.browse(values['type'])
            values['step'] = type.get_first_step()
        values['progress'] = (self.step.browse(values['step']).progress
                              if values['step'] else 0.0)
        return super(ContractWithStep, self).create(values)

    step = fields.Many2one(
        'rea.contract.step',
        'Step',
        select=True,
        domain="[('type','=',type)]")


class ContractTypeWithStep(models.Model):
    _inherit = 'rea.contract.type'

    def get_first_step(self):
        """ Return the id of the first step of a type"""
        if len(self) == 0:
            return False
        steps = [(s.progress, s.id) for s in self.step_ids]
        return sorted(steps)[0][1] if len(steps) else False

    step_ids = fields.One2many(
        'rea.contract.step',
        'type',
        'Steps',
        copy=True,
        help="The steps associated to this type")
