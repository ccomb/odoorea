from odoo import fields, models, tools, _
from odoo.exceptions import UserError


class Event(models.Model):
    """ Exchange or conversion of economic Resources by economic Agents
    """
    _name = 'rea.event'
    _description = "Event"
    _inherit = ['rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

    name = fields.Char(
        string="name",
        required=True,  # TODO configurable?
        default=lambda self: _('New'),
        index=True
    )
    type = fields.Many2one(
        'rea.event.type',
        string="Type",
        ondelete='restrict')
    groups = fields.Many2many(
        'rea.event.group',
        string="Groups")
    date = fields.Date(
        "Actual date")
    commitments = fields.Many2many(
        'rea.commitment',
        string="Events",
        help="Commitments fulfilled by this event")
    quantity = fields.Float(
        string="Quantity")
    resource_type = fields.Many2one(
        'rea.resource.type',
        string="Resource Type")
    resource = fields.Many2one(
        'rea.resource',
        string="Resource")
    provider = fields.Many2one(
        'rea.agent',
        string="Provider")
    receiver = fields.Many2one(
        'rea.agent',
        string="Receiver")
    inflow = fields.Many2one(
        'rea.resource',
        string="Inflow")
    outflow = fields.Many2one(
        'rea.resource',
        string="Outflow")
    kind = fields.Selection(
        [('increment', 'Increment'),
         ('decrement', 'Decrement'),
         ('external', 'External'),
         ('internal', 'Internal')],
        compute='_kind',
        string="Kind")

    _sql_contraints = [
        ('unique_event_name', 'unique(name)',
         'Another event with the same name already exists.'),
    ]

    def _kind(self):
        if not self.env.user.company:
            raise UserError('No REA company configured for current user')
        for event in self:
            if event.provider == self.env.user.company:
                if event.receiver != self.env.user.company:
                    event.kind = 'decrement'
                else:
                    event.kind = 'internal'
            else:
                if event.receiver == self.env.user.company:
                    event.kind = 'increment'
                else:
                    event.kind = 'external'

    #def create(self):
    #    """ During the create we run the hooks of the aspects that modify the
    #    attributes corresponding to the exchange or conversion.
    #    For example an 'owner' property during an exchange process.
    #    Also run the hooks of the aspects that modify a defined field
    #    such as an identifier
    #    """
    #    # get the identifier from the type
    #    for ident_type in self.type.identifiers:
    #        udent_type

    #    return super(Event, self).create()


class EventType(models.Model):
    """ Abstract definition of actual events
    """
    _name = 'rea.event.type'
    _description = "Event Type"
    _parent_name = 'type'
    _inherit = ['rea.type.identifier',
                'rea.type.lifecycle',
                'rea.type.property',
                'rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)
    _parent_name = 'type'

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    code = fields.Char(
        string="Code",
        required=True,
        help=u"arbitrary technical code",
        index=True)
    type = fields.Many2one(
        'rea.event.type',
        string="Type",
        ondelete='restrict')
    subtypes = fields.One2many(
        'rea.event.type',
        'type',
        copy=True,
        string="Sub-types")
    structural = fields.Boolean(
        'Structural type?',
        help="Hide in operational choices?")
    kind = fields.Selection(
        [('increment', 'Increment'),
         ('decrement', 'Decrement')],
        string="Kind")
    provider_type = fields.Many2one(
        'rea.agent.type',
        string="Provider Type")
    receiver_type = fields.Many2one(
        'rea.agent.type',
        string="Receiver Type")
    resource_type = fields.Many2one(
        'rea.resource.type',
        string="Resource Type")

    _sql_contraints = [
        ('unique_event_type_code', 'unique(code)',
         'Another event type with the same code already exists.'),
    ]

# TODO : l'event type est proche de la
# notion de journal et peut avoir une
# correspondance en compta


class EventGroup(models.Model):
    """ Group of events
    """
    _name = 'rea.event.group'
    _description = "Event Group"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
