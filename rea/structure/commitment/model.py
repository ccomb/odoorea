from odoo import fields, models, api, tools, _
from odoo.exceptions import ValidationError, UserError


class Commitment(models.Model):
    """ Promise of economic Event at a future or unknown date
    """
    _name = 'rea.commitment'
    _description = "Commitment"
    _inherit = ['rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)
    _lifecycle_actions = [('fulfill', 'Fulfill the commitment')]

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
        return self.contract.parties.browse(False)

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
        return self.contract.parties.browse(False)

    name = fields.Char(
        string="Name",
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

    _sql_contraints = [
        ('unique_commitment_name', 'unique(name)',
         'Another commitment with the same name already exists.'),
    ]

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


class CommitmentType(models.Model):
    """ Astract definition of actual commitments
    """
    _name = 'rea.commitment.type'
    _description = "Commitment Type"
    _parent_name = 'type'
    _inherit = ['rea.type.identifier',
                'rea.type.lifecycle',
                'rea.type.property',
                'rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

    name = fields.Char(
        string=u"name",
        required=True,
        index=True)
    code = fields.Char(
        string="Code",
        required=True,
        help=u"arbitrary technical code",
        index=True)
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
    kind = fields.Selection([
        ('increment', 'Increment'),
        ('decrement', 'Decrement')],
        string=u"Kind")
    contract_type = fields.Many2one(
        'rea.contract.type',
        string=u"Contract Type")
    event_type = fields.Many2one(
        'rea.event.type',
        string=u"Event Type",
        help="Type of the events corresponding to this type of commitments")
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

    _sql_contraints = [
        ('unique_commitment_type_code', 'unique(code)',
         'Another commitment type with the same code already exists.'),
    ]

    def create_event_type(self):
        """Create an event type similar to this commitment type
        """
        results = []
        for ct in self:
            if ct.event_type:
                raise UserError("Event type is already set")
            EVENT_TYPE = self.env['rea.event.type']
            event_type_type = None
            event_type_types = EVENT_TYPE.search([('code', '=', ct.code)])
            if len(event_type_types) == 1:
                event_type_type = event_type_types[0]
            event_type = EVENT_TYPE.create({
                'name': ct.name,
                'code': ct.code,
                'type': event_type_type and event_type_type.id or False,
                'structural': ct.structural,
                'kind': ct.kind,
                'provider_type': ct.provider_type.id,
                'receiver_type': ct.receiver_type.id,
                'resource_types': [(6, 0, ct.resource_types.ids)],
                })
            results.append(event_type.id)
            ct.write({'event_type': event_type.id})
        return results


class CommitmentGroup(models.Model):
    """ Group of commitments
    """
    _name = 'rea.commitment.group'
    _description = "Commitment Group"

    name = fields.Char(
        string="Name",
        required=True,
        index=True)
