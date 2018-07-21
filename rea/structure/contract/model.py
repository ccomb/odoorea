# coding: utf-8
from odoo import fields, models, api, tools, _
from odoo.exceptions import ValidationError
from time import strftime
from . import combinator
from itertools import groupby


class Contract(models.Model):
    """ Set of commitments and terms forming clauses
    """
    _name = 'rea.contract'
    _description = "Contract"
    _inherit = ['rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

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

    @api.depends('clauses')
    def _totals(self):
        """compute the grouped totals for the contract footer
        """
        for c in self:
            company = self.env.user.company
            inclauses = sorted(
                            ((c.type, c.resource_type, c.quantity)
                             for c in c.clauses if c.receiver == company),
                            key=lambda x: (x[0].name, x[0].id))
            insums = [gr[0] + (str(sum(g[2] for g in gr[1])),)
                      for gr in groupby(inclauses, lambda c: c[0:2])]
            inclauses2 = sorted(
                            ((c.type, c.resource_type, c.quantity)
                             for c in c.clauses if c.receiver == company),
                            key=lambda x: x[1])
            intotals = [(gr[0], str(sum(g[2] for g in gr[1])))
                        for gr in groupby(inclauses2, lambda c: c[1])]
            outclauses = sorted((c.type, c.resource_type, c.quantity)
                                for c in c.clauses if c.provider == company)
            outsums = [gr[0] + (str(sum(g[2] for g in gr[1])),)
                       for gr in groupby(outclauses, lambda c: c[0:2])]
            outclauses2 = sorted(
                            ((c.type, c.resource_type, c.quantity)
                             for c in c.clauses if c.provider == company),
                            key=lambda x: x[1])
            outtotals = [(gr[0], str(sum(g[2] for g in gr[1])))
                         for gr in groupby(outclauses2, lambda c: c[1])]
            c.totals = ('<table style="float: right; text-align: right">' +
                        ('<tr><th style="text-align: right">Decrements:</th>'
                         '<th style="text-align: right">Increments:</th></tr>'
                         if outsums or insums else '') +
                        '<tr><td style="vertical-align: top">' +
                        '<br/>'.join(["%s: <b>%s %s</b>"
                                      % (k[0].name, k[2], k[1].name)
                                      for k in outsums]) + '<br/>' +
                        '<br/>'.join(["<b>%s: %s %s</b>"
                                      % (c.type.dtotal_label, k[1], k[0].name)
                                      for k in outtotals]) + '</td>' +
                        '<td style="vertical-align: top; padding-left: 1em">' +
                        '<br/>'.join(["%s: <b>%s %s</b>"
                                      % (k[0].name, k[2], k[1].name)
                                      for k in insums]) + '<br/>' +
                        '<br/>'.join(["<b>%s: %s %s</b>"
                                      % (c.type.itotal_label, k[1], k[0].name)
                                      for k in intotals]) +
                        '</td></tr></table>')

    name = fields.Char(
        string="name",
        required=True,
        default=lambda self: _('New'),
        index=True)
    type = fields.Many2one(
        'rea.contract.type',
        required=True,
        string="Type",
        ondelete='restrict')
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
        string="Clauses",
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
    totals = fields.Html(
        string="Inflow",
        readonly=True,
        compute='_totals')

    def copy(self, default=None):
        # signal the commitment creation to not execute terms
        return super(Contract, self.with_context(
            {'no_term_exec': True})).copy(default)


class ContractType(models.Model):
    """ Abstract definition of actual contracts
    """
    _name = 'rea.contract.type'
    _description = "Contract Type"
    _parent_name = 'type'
    _inherit = ['rea.type.identifier',
                'rea.type.lifecycle',
                'rea.type.property',
                'rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)
    _parent_name = 'type'

    type = fields.Many2one(
        'rea.contract.type',
        string="Type",
        ondelete='restrict')
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
    itotal_label = fields.Char(
        string="Total label for increments",
        required=True,
        default="Increment Totals")
    dtotal_label = fields.Char(
        string="Total label for decrements",
        required=True,
        default="Decrement Totals")


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

    name = fields.Char(
        "Name",
        required=True,
        help="Name of the variable used in the expression of the action")
    type = fields.Selection([
        ('konst', 'Constant'),
        ('days', 'Days after'),
        ('time', 'Current Time'),
        ('rea.commitment', 'Field of the Commitment'),
        ('rea.resource.type', 'Field of the Resource Type'),
        ('model.rea.resource.type', 'Resource Type'),
        ('rea.resource.conversion.type', 'Resource Conversion')])
    konst = fields.Float("Value")
    date = fields.Date("Date")
    field = fields.Many2one(
        'ir.model.fields',
        "Field")
    term = fields.Many2one(
        'rea.contract.term',
        "Contract Term")
    resource_type = fields.Many2one(
        'rea.resource.type',
        "Resource type")
    conversion_type = fields.Many2one(
        'rea.resource.conversion.type',
        "Conversion Type")

    def value(self, commitment):
        """ get the value of the observable
        """
        if self.type == 'konst':
            return self.konst
        if self.type == 'rea.commitment':
            return getattr(commitment, self.field.name)
        if self.type == 'rea.resource.type':
            return getattr(commitment.resource_type, self.field.name)
        if self.type == 'model.rea.resource.type':
            return self.resource_type.id
        if self.type == 'rea.resource.conversion.type':
            conversion = self.env['rea.resource.conversion']
            return conversion.convert(
                self.conversion_type, commitment.resource_type)
        raise NotImplementedError


class ContractTerm(models.Model):
    """ What happens if clauses are not fullfilled
    (generate additional commitments)
    """
    _name = 'rea.contract.term'
    _description = "Contract term"

    name = fields.Char(
        string="name",
        required=True)
    contract = fields.Many2one(
        'rea.contract',
        string="Contract")
    expression = fields.Char(
        "Expression",
        help=("Expression used to create the commitment "
              "using the following functions:\n"
              "Zero\n"
              "One\n"
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
    provider_choice = fields.Selection([
        ('commitment', "Same as the triggering commitment"),
        ('contract', "Same as the triggering contract (not implemented yet)"),
        ('default', "Default provider of the commitment"),
        ('select', "Select...")])
    commitment_provider = fields.Many2one(
        'rea.agent',
        string="Chosen Provider",
        help="The provider of the commitment generated by the expression")
    receiver_choice = fields.Selection([
        ('commitment', "Same as the triggering commitment"),
        ('contract', "Same as the triggering contract (not implemented yet)"),
        ('default', "Default receiver of the commitment"),
        ('select', "Select...")])
    commitment_receiver = fields.Many2one(
        'rea.agent',
        string="Chosen Receiver",
        help="The receiver of the commitment generated by the expression")
    contract_choice = fields.Selection([
        ('term', 'Same contract as this term'),
        ('commitment', 'Same contract as the triggering commitment'),
        ('select', 'Select...')])
    commitment_contract = fields.Many2one(
        'rea.contract',
        string="Chosen Contract",
        help="The contract linked to the generated commitment")
    condition_resource_types = fields.Many2many(
        'rea.resource.type',
        string='Resource type',
        help="One of these resource types must be used "
             "in the triggering commitment.")
    condition_commitment_types = fields.Many2many(
        'rea.commitment.type',
        string='Commitment type',
        help="The triggering commitment must be one of this types")
    commitment_type = fields.Many2one(
        'rea.commitment.type',
        string='Commitment type',
        help="Type of the generated commitment")
    globalscope = fields.Boolean(
        "Global scope?",
        help="This term applies to all contracts")
    condition_resource_groups = fields.Many2many(
        'rea.resource.group',
        string="Resource Groups",
        help="Restrict this contract term to commitments "
             "whose resource groups are one of these")

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
            # TODO memoize and use a resolution (day, minute, etc.)
            # to avoid recreating the commitment at each term execution
            try:
                contract_function = eval(t.expression,
                                         {"__builtins__": {}},
                                         lcls)
            except Exception as e:
                raise ValidationError(
                    "The expression \"%s\" used in the term \"%s\" "
                    "of the contract \"%s\" has an error : %s"
                    % (t.expression, t.name, t.contract.name, str(e)))
            # attributes of the created commitment depends on the config
            provider_id = (
                commitment.provider.id if t.provider_choice == 'commitment'
                else NotImplemented if t.provider_choice == 'contract'
                else commitment._default_provider().id
                or t.commitment_provider.id
                if t.provider_choice == 'default'
                else t.commitment_provider.id)
            receiver_id = (
                commitment.receiver.id if t.receiver_choice == 'commitment'
                else NotImplemented if t.receiver_choice == 'contract'
                else commitment._default_receiver().id
                or t.commitment_receiver.id
                if t.receiver_choice == 'default'
                else t.commitment_receiver.id)
            contract_id = (
                commitment.contract.id if t.contract_choice == 'commitment'
                else t.contract.id if t.contract_choice == 'term'
                else t.commitment_contract.id)
            commitments = contract_function(
                strftime('%Y-%m-%d %H:%M:%S'), provider_id, receiver_id)
            for c in commitments:
                if not c:
                    continue
                executing = self.env.context.get('executing_terms')
                executing = [] if executing is None else executing.split(':')
                if str(t.id) in executing:
                    # avoid infinite recursion
                    continue
                else:
                    executing.append(str(t.id))
                #c['date'] = c['acquisition_date']
                c['contract'] = contract_id
                c['type'] = t.commitment_type.id
                c = self.env['rea.commitment'].with_context(
                    {'executing_terms':
                     ':'.join({str(i) for i in executing})}).create(c)
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
            if (term.condition_resource_groups and
                set(c.resource_type.groups
                    ).isdisjoint(set(term.condition_resource_groups))):
                    continue
            if (term.condition_commitment_types and
               all([ct not in c.type.search([('id', 'parent_of', c.type.id)])
                    for ct in term.condition_commitment_types])):
                continue
            if (term.condition_resource_types and
                all([rt not in c.resource_type.search(
                    [('id', 'parent_of', c.resource_type.id)])
                    for rt in term.condition_resource_types])):
                continue
            if not self.env.context.get('no_term_exec'):
                term.execute(c)
        return c
