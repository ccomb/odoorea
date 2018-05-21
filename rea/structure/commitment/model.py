from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Commitment(models.Model):
    """ Promise of economic Event at a future or unknown date
    """
    _name = 'rea.commitment'
    _description = "Commitment"
    _inherit = ['rea.lifecycleable.entity',
                'rea.identifiable.entity',
                'rea.propertyable.entity']

    def _default_provider(self):
        for agent in self.contract.parties:
            if self.env.user.company == agent:
                if self.type.kind == 'decrement':
                    return agent
            else:
                if (self.type.kind == 'increment'
                        and self.type.provider_type in agent.type.search(
                        [('id', 'parent_of', agent.type.id)])):
                    return agent

    def _default_receiver(self):
        for agent in self.contract.parties:
            if self.env.user.company == agent:
                if self.type.kind == 'increment':
                    return agent
            else:
                if (self.type.kind == 'decrement'
                        and self.type.receiver_type in agent.type.search(
                        [('id', 'parent_of', agent.type.id)])):
                    return agent

    name = fields.Char(
        string="name",
        required=True,
        default=lambda self: _('New'),
        index=True)
    type = fields.Many2one(
        'rea.commitment.type',
        domain="[('contract_type', 'parent_of', contract_type),"
               "('structural', '=', False)]",
        string="Type",
        ondelete='restrict')
    groups = fields.Many2many(
        'rea.commitment.group',
        string="Groups")
    date = fields.Date(
        "Expected date")
    events = fields.Many2many(
        'rea.event',
        string="Events",
        help="Events fulfilling this commitment")
    quantity = fields.Float(
        string="Quantity")
    # TODO uom ?
    resource_type = fields.Many2one(
        'rea.resource.type',
        domain="[('id', 'child_of', type_resource_types[0][2]),"
               " ('structural', '=', False)]",
        string="Resource Type")
    reserved_resources = fields.Many2many(
        'rea.resource',
        domain="[('type', 'parent_of', resource_type)]",
        string="Reserved Resources")
    contract = fields.Many2one(
        'rea.contract',
        string="Contract",
        copy=False,
        ondelete='cascade')
    contract_type = fields.Many2one(  # just for a domain
        'rea.contract.type',
        compute='_contract_type')
    type_resource_types = fields.Many2many(  # just for a domain
        'rea.resource.type',
        compute='_type_resource_types')
    provider = fields.Many2one(
        'rea.agent',
        default=_default_provider,
        string="Provider")
    receiver = fields.Many2one(
        'rea.agent',
        default=_default_receiver,
        string="Receiver")
    autofulfill = fields.Boolean(  # TODO
        u"Automatic",
        help=u"Automatically fulfill to an event at due date")

    @api.onchange('type')
    def _change_type(self):
        for commitment in self:
            commitment.receiver = commitment._default_receiver()
            commitment.provider = commitment._default_provider()
        return {'domain': {'resource_type':
                [('id', 'child_of', [t.id for t in self.type.resource_types]),
                 ('structural', '=', False)]}}

    @api.constrains('reserved_resources')
    def _check_reserved_resources(self):
        for commitment in self:
            for resource in commitment.reserved_resources:
                nb_reservations = len(resource.reserved)
                max_reservations = resource.type.max_reservations
                if nb_reservations > max_reservations:
                    raise ValidationError(
                        "Selected resource is not available")

    @api.depends('contract')
    def _contract_type(self):
        for commitment in self:
            commitment.contract_type = commitment.contract.type

    def _type_resource_types(self):
        for commitment in self:
            commitment.type_resource_types = commitment.type.resource_types

    def fulfill(self, amount=None, ratio=None):
        """Create the full event if no args are given
        Otherwise create a partial event corresponding to the amount or ratio
        """
        raise NotImplementedError  # TODO
        for c in self:
            commitment = c.read()
            self.env['rea.event'].create(commitment)


class CommitmentType(models.Model):
    """ Astract definition of actual commitments
    """
    _name = 'rea.commitment.type'
    _description = "Commitment Type"
    _parent_name = 'type'
    _inherit = ['rea.identifiable.type',
                'rea.lifecycleable.type',
                'rea.propertyable.type',
                'rea.lifecycleable.entity',
                'rea.identifiable.entity',
                'rea.propertyable.entity']

    type = fields.Many2one(
        'rea.commitment.type',
        string="Type",
        ondelete='restrict')
    subtypes = fields.One2many(
        'rea.commitment.type',
        'type',
        copy=True,
        string="Sub-types")
    structural = fields.Boolean(
        'Structural type?',
        help="Hide in operational choices?")
    name = fields.Char(
        string=u"name",
        required=True,
        index=True)
    kind = fields.Selection([
        ('increment', 'Increment'),
        ('decrement', 'Decrement')],
        string=u"Kind")
    contract_type = fields.Many2one(
        'rea.contract.type',
        string=u"Contract Type")
    provider_type = fields.Many2one(
        'rea.agent.type',
        string=u"Provider Type")
    receiver_type = fields.Many2one(
        'rea.agent.type',
        string=u"Receiver Type")
    resource_types = fields.Many2many(
        'rea.resource.type',
        string=u"Resource types",
        help=u"Resource Types permitted for this commitment type")
    resource_groups = fields.Many2one(
        'rea.resource.group',
        string="Resource Groups permitted for this commitment type")
    autofulfill = fields.Boolean(  # TODO
        u"Automatic",
        help=u"Automatically fulfill to events at due date")


class CommitmentGroup(models.Model):
    """ Group of commitments
    """
    _name = 'rea.commitment.group'
    _description = "Commitment Group"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
