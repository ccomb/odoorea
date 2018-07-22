from odoo import fields, models, api, tools
from odoo.exceptions import ValidationError, UserError


class DualityType(models.Model):
    """Set of event types bound by a duality relationship.
    Abstract definition of actual Dualities.
    It contains the rules of the duality.
    It can also be seen as a business 'deal'
    (was previously named process)
    """
    _name = 'rea.duality.type'
    _description = 'Duality Type'
    _inherit = ['rea.type.identifier',
                'rea.type.lifecycle',
                'rea.type.property',
                'rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    code = fields.Char(
        string="Code",
        required=True,
        help=u"Arbitrary technical code",
        index=True)
    type = fields.Many2one(
        'rea.duality.type',
        string="Duality Type")
    subtypes = fields.One2many(
        'rea.duality.type',
        'type',
        copy=True,
        string="Sub-types")
    kind = fields.Selection([
        ('exchange', "Exchange"),
        ('conversion', "Conversion")],
        string="Kind")
    event_types = fields.Many2many(
        'rea.event.type',
        string="Event Types")

    # for each process type, create an action button to start a new process

    _sql_contraints = [
        ('unique_duality_type_code', 'unique(code)',
         'Another duality type with the same code already exists.'),
    ]


class DualityGroup(models.Model):
    """ Group of dualities
    Allows to gather dualities as a business unit
    """
    _name = 'rea.duality.group'
    _description = "Duality Group"

    name = fields.Char(
        string="Name",
        required=True,
        index=True)
    groups = fields.Many2one(
        'rea.duality.group',
        string="Group")


class Duality(models.Model):
    """ Set of partial events bound by a duality relationship.
    """
    _name = 'rea.duality'
    _description = 'Duality'
    _inherit = ['rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

    name = fields.Char(
        string="Name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.duality.type',
        string="Duality Type")
    partial_events = fields.One2many(
        'rea.duality.event',
        'duality',
        string="Partial events")

    def unlink(self):
        for d in self:
            events = [p.event for p in d.partial_events]
            super(Duality, d).unlink()
            for event in events:
                # force recompute as it is not triggered
                event.write(
                    {'duality_balance':
                        event.quantity - sum(
                            p.quantity for p in event.duality_partial_events)})

    _sql_contraints = [
        ('unique_duality_name', 'unique(name)',
         'Another duality with the same name already exists.'),
    ]


class PartialEvent(models.Model):
    """Partial event used in the duality relationship
    """
    _name = 'rea.duality.event'
    _description = "Partial Event for Duality Relationship"

    duality = fields.Many2one(
        'rea.duality',
        ondelete='cascade')
    event = fields.Many2one(
        'rea.event',
        required=True,
        string="Event")
    quantity = fields.Float(
        required=True,
        string="Quantity")

    resource_type = fields.Many2one(
        'rea.resource.type',
        related='event.resource_type',
        readonly=True,
        string="Resource Type")

    def unlink(self):
        for p in self:
            duality = p.duality
            super(PartialEvent, p).unlink()
            if len(duality.partial_events) == 0:
                duality.unlink()
            events = self.env['rea.event'].browse(
                [p.event.id for p in duality.partial_events])
            events.check_duality()

    @api.onchange('event')
    def onchange_event(self):
        for p in self:
            p.quantity = p.event.duality_balance

    @api.constrains('quantity')
    def constrain_quantity(self):
        for p in self:
            if p.quantity > p.event.quantity:
                raise ValidationError(
                    'Assigned quantity higher than related event %s',
                    p.event.name)
            if p.quantity <= 0:
                raise ValidationError(
                    'Assigned quantity cannot be zero or negative')


class Event(models.Model):
    """add partial_event info on the event
    """
    _inherit = 'rea.event'

    duality_partial_events = fields.One2many(
        'rea.duality.event',
        'event',
        string="Partial events",
        help="Partial quantities linked together in a duality relationship")
    duality_balance = fields.Float(
        "Unreconciled",
        compute='_duality_balance',
        store=True)

    @api.depends('duality_partial_events', 'quantity')
    def _duality_balance(self):
        for event in self:
            # check that the event is reconciled
            assigned = sum(p.quantity for p in event.duality_partial_events)
            event.duality_balance = event.quantity - assigned

    def check_duality(self):
        """check the validity of the dualiy
        """
        agents = {}
        for e in self:
            agents.setdefault(e.provider.id, {'r': 0, 'p': 0})
            agents.setdefault(e.receiver.id, {'r': 0, 'p': 0})
            agents[e.provider.id]['p'] += 1
            agents[e.receiver.id]['r'] += 1
        if any(any([i['r'] == 0, i['p'] == 0]) for i in agents.values()):
            raise ValidationError(
                u"Invalid duality: "
                u"at least one agent is not both a receiver and a provider")
        if len(self) < 2:
            raise ValidationError(
                u"Invalid duality: "
                u"two events or more should be selected")


class DualityWizard(models.TransientModel):
    """Wizard used to link events by a duality relationship
    (such as a reconciliation)
    """
    _name = 'rea.duality.reconciliation.wizard'

    def _duality_partial_events(self):
        ids = self.env.context.get('active_ids')
        if not ids or self.env.context.get('norecs'):
            return []
        events = self.env['rea.event'].browse(ids)
        events.check_duality()
        rec_ids = []
        for e in events:
            if e.duality_balance <= 0:
                continue
            rec = self.with_context(
                {'norecs': True}
            ).create(
                {'event': e.id, 'quantity': e.duality_balance})
            rec_ids.append(rec.id)
        if not rec_ids:
            raise UserError(u"Nothing to reconcile")
        return [(6, 0, rec_ids)]

    duality_type = fields.Many2one(
        'rea.duality.type')
    event = fields.Many2one(
        'rea.event',
        string="Event")
    provider = fields.Many2one(
        'rea.agent',
        related='event.provider',
        readonly=True)
    receiver = fields.Many2one(
        'rea.agent',
        related='event.receiver',
        readonly=True)
    quantity = fields.Float(
        string="Quantity")
    resource_type = fields.Many2one(
        'rea.resource.type',
        related='event.resource_type',
        readonly=True,
        string="Resource Type")

    duality = fields.Many2one(
        'rea.duality.reconciliation.wizard',
        string="Duality")
    duality_partial_events = fields.One2many(
        'rea.duality.reconciliation.wizard',
        'duality',
        default=_duality_partial_events,
        string="Partial events")

    def save_duality(self):
        duality = self.env['rea.duality'].create(
            {'type': self.duality_type.id})
        if not duality.name:
            raise UserError(u"Please configure "
                            u"an automatic numbering for dualities")
        for p in self.duality_partial_events:
            records = p.read(load='_classic_write')
            if len(records) != 1:
                raise UserError("Wizard bug, should not happen")
            record = records[0]
            record['duality'] = duality.id
            self.env['rea.duality.event'].create(record)
        events = self.env['rea.event'].browse(
            [p.event.id for p in duality.partial_events])
        events.check_duality()
