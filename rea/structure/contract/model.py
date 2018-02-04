# coding: utf-8
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from time import strftime
from . import combinator


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

    @api.one
    @api.constrains('parties')
    def _change_parties(self):
        for c in self:
            if len(c.parties) > c.type.max_parties > 0:
                raise ValidationError(
                    u"This type of contract cannot have more than {} parties"
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
        string="Terms",
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
    _parent_name = 'type'

    type = fields.Many2one(
        'rea.contract.type',
        string="Type")
    structural = fields.Boolean(
        'Structural type?',
        help="Hide in operational choices?")
    name = fields.Char(
        string="Contract Type",
        required=True,
        index=True)
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


class Observable(models.Model):
    _name = 'rea.contract.observable'
    _description = "Observable for contracts"

    sequence = fields.Integer("Sequence")
    name = fields.Char("Name")
    type = fields.Selection([
        ('konst', 'Constant'),
        ('days', 'Days after'),
        ('time', 'Current Time'),
        ('field', 'Commitment Field')])
    konst = fields.Float("Value")
    date = fields.Date("Date")
    field = fields.Char("Field name")
    term = fields.Many2one(
        'rea.contract.term',
        "Contract Term")

    def value(self, commitment):
        if self.type == 'konst':
            return self.konst
        if self.type == 'field':
            return getattr(commitment, self.field)
        raise NotImplementedError


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
    expression = fields.Char(
        "Expression",
        help=("Zero()\n"
              "One(resource_type)\n"
              "Give(cs)\n"
              "And(cs1, cs2)\n"
              "Scale(obs, cs)\n"
              "When(obs, cs)\n"
              "Or(cs1, cs2)\n"
              "Cond(obs, cs1, cs2)\n"
              "Truncate(obs, cs)\n"
              "Then(cs1, cs2)\n"
              "Get(cs)\n"
              "Anytime(cs)\n"))
    commitments = fields.Many2many(
        'rea.commitment',
        string="Generated commitments",
        help="Commitments generated by this Term")
    observables = fields.One2many(
        'rea.contract.observable',
        'term',
        string="Observables")
    provider = fields.Many2one(
        'rea.agent',
        string="Provider")
    receiver = fields.Many2one(
        'rea.agent',
        string="Receiver")

    resource_type = fields.Many2one(
        'rea.resource.type',
        string='Resource type',
        help="This resource type must be used in the originating commitment.")

    commitment_type = fields.Many2one(
        'rea.commitment.type',
        string='Commitment type',
        help="Type of the generated commitment")

    globalscope = fields.Boolean("Global scope?")
    resource_groups = fields.Many2many(
        'rea.resource.group',
        string="Resource Groups",
        help="Restrict the term to commitments whose resource groups "
             "are on of these")

    def execute_all_terms(self):
        for t in self:
            for c in t.contract.clauses:
                self.execute(c)

    def execute(self, commitment):
        for t in self:
            # FIXME unsafe
            lcls = {o.name: o.value(commitment) for o in t.observables}
            for c in [c for c in dir(combinator) if not c.startswith('_')]:
                lcls[c] = getattr(combinator, c)
            lcls['resource_type'] = commitment.resource_type.id
            # TODO memoize and use a resolution (day, minute, etc.)
            # to avoid recreating the commitment at each term execution
            contract_function = eval(t.expression,
                                     {"__builtins__": {}},
                                     lcls)
            commitments = contract_function(
                strftime('%Y-%m-%d %H:%M:%S'), t.provider, t.receiver)
            print(commitments)
            for c in commitments:
                if not c:
                    continue
                if self.env.context.get('term_execution') == t.id:
                    # avoid infinite recursion
                    continue
                #c['date'] = c['acquisition_date']
                c['contract'] = commitment.contract.id
                c['type'] = t.commitment_type.id
                c['provider'] = t.provider.id
                c['receiver'] = t.receiver.id
                print(c)
                c = self.env['rea.commitment'].with_context(
                    {'term_execution': t.id}).create(c)
                t.write({'commitments': [(4, c.id)]})

# TODO ClauseType ??


class Commitment(models.Model):
    _inherit = 'rea.commitment'

    @api.model
    def create(self, vals):
        """trigger the check of the current contract terms and global ones
        """
        c = super(Commitment, self).create(vals)
        globalterms = c.contract.terms.search([('globalscope', '=', True)])
        for term in c.contract.terms + globalterms:
            # execute the terms if one of the resource groups
            # belongs to the configured resource groups on the term
            if (term.resource_groups and
                set(c.resource_type.groups
                    ).isdisjoint(set(term.resource_groups))):
                    continue
            if term.resource_type and term.resource_type not in c.resource_type.search([('id', 'parent_of', c.resource_type.id)]):
                continue
            term.execute(c)
        return c
