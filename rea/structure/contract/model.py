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
    _inherit = ['rea.lifecycleable.entity',
                'rea.identifiable.entity',
                'rea.propertyable.entity']

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
        'rea.commitment',
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


class ContractType(models.Model):
    """ Abstract definition of actual contracts
    """
    _name = 'rea.contract.type'
    _description = "Contract Type"
    _parent_name = 'type'
    _inherit = ['rea.identifiable.type',
                'rea.lifecycleable.type',
                'rea.propertyable.type',
                'rea.lifecycleable.entity',
                'rea.identifiable.entity',
                'rea.propertyable.entity']
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

    @api.depends('term')
    def _term_resource_type(self):
        for o in self:
            o.term_resource_type = o.term.condition_resource_type

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
    _description = "REA Contract term"

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
    provider = fields.Many2one(
        'rea.agent',
        string="Provider",
        help="The provider of the commitment generated by the expression")
    receiver = fields.Many2one(
        'rea.agent',
        string="Receiver",
        help="The receiver of the commitment generated by the expression")
    condition_resource_type = fields.Many2one(
        'rea.resource.type',
        string='Resource type',
        help="This resource type must be used in the originating commitment.")
    condition_commitment_type = fields.Many2one(
        'rea.commitment.type',
        string='Commitment type',
        help="The originating commitment must be of this type.")
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
                    "The contract \"%s\" has an error in the expression used"
                    " in the term \"%s\":\n\n%s\n\nThe error is: %s"
                    % (t.contract.name, t.name, t.expression, str(e)))
            commitments = contract_function(
                strftime('%Y-%m-%d %H:%M:%S'), t.provider, t.receiver)
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
                c['contract'] = commitment.contract.id
                c['type'] = t.commitment_type.id
                c['provider'] = t.provider.id
                c['receiver'] = t.receiver.id
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
            if (term.condition_commitment_type and
               term.condition_commitment_type != c.type):
                continue
            if (term.condition_resource_type and term.condition_resource_type
               not in c.resource_type.search(
                   [('id', 'parent_of', c.resource_type.id)])):
                continue
            term.execute(c)
        return c
