from odoo import fields, models, api, tools
from odoo.exceptions import ValidationError, UserError


class FulfillmentType(models.Model):
    """Link type between events and commitments
    Abstract definition of the actual link
    It contains the rules of the fulfillment.
    """
    _name = 'rea.fulfillment.type'
    _description = 'Fulfillment Type'
    _inherit = ['rea.type.identifier',
                'rea.type.lifecycle',
                'rea.type.property',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.fulfillment.type',
        string="Fulfillment Type")
    subtypes = fields.One2many(
        'rea.fulfillment.type',
        'type',
        copy=True,
        string="Sub-types")
    event_types = fields.Many2many(
        'rea.event.type',
        string="Event Types")
    commitment_types = fields.Many2many(
        'rea.commitment.type',
        string="Commitment Types")


class FulfillmentGroup(models.Model):
    """ Group of fulfillments
    Allows to gather fulfillments as a logical unit
    """
    _name = 'rea.fulfillment.group'
    _description = "Fulfillment Group"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    groups = fields.Many2one(
        'rea.fulfillment.group',
        string="Group")


class Fulfillment(models.Model):
    """ Set of partial events and commitments
    """
    _name = 'rea.fulfillment'
    _description = 'Fulfillment'
    _inherit = ['rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.fulfillment.type',
        string="Fulfillment Type")
    partial_events = fields.One2many(
        'rea.fulfillment.event',
        'fulfillment',
        string="Partial events")
    partial_commitments = fields.One2many(
        'rea.fulfillment.commitment',
        'fulfillment',
        string="Partial commitments")

    def unlink(self):
        for d in self:
            events = [p.event for p in d.partial_events]
            commitments = [p.event for p in d.partial_commitments]
            super(Fulfillment, d).unlink()
            # force recompute as it is not triggered
            for commitment in commitments:
                commitment.write(
                    {'fulfillment_balance':
                        commitment.quantity - sum(
                            p.quantity for p in commitment.fulfillment_partial_commitments)})
            for event in events:
                event.write(
                    {'fulfillment_balance':
                        event.quantity - sum(
                            p.quantity for p in event.fulfillment_partial_events)})


class PartialEvent(models.Model):
    """Partial event used in the fulfillment relationship
    """
    _name = 'rea.fulfillment.event'
    _description = "Partial Event for Fulfillment Relationship"

    fulfillment = fields.Many2one(
        'rea.fulfillment',
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
            fulfillment = p.fulfillment
            super(PartialEvent, p).unlink()
            if len(fulfillment.partial_events) == 0:
                fulfillment.unlink()
            events = self.env['rea.event'].browse(
                [p.event.id for p in fulfillment.partial_events])
            events.check_fulfillment()

    @api.onchange('event')
    def onchange_event(self):
        for p in self:
            p.quantity = p.event.fulfillment_balance

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


class PartialCommitment(models.Model):
    """Partial commitment used in the fulfillment relationship
    """
    _name = 'rea.fulfillment.commitment'
    _description = "Partial Commitment for Fulfillment Relationship"

    fulfillment = fields.Many2one(
        'rea.fulfillment',
        ondelete='cascade')
    commitment = fields.Many2one(
        'rea.commitment',
        required=True,
        string="Commitment")
    quantity = fields.Float(
        required=True,
        string="Quantity")
    resource_type = fields.Many2one(
        'rea.resource.type',
        related='commitment.resource_type',
        readonly=True,
        string="Resource Type")

    def unlink(self):
        for p in self:
            fulfillment = p.fulfillment
            super(PartialCommitment, p).unlink()
            if len(fulfillment.partial_commitments) == 0:
                fulfillment.unlink()
            commitments = self.env['rea.commitment'].browse(
                [p.commitment.id for p in fulfillment.partial_commitments])
            commitments.check_fulfillment()

    @api.onchange('commitment')
    def onchange_commitment(self):
        for p in self:
            p.quantity = p.commitment.fulfillment_balance

    @api.constrains('quantity')
    def constrain_quantity(self):
        for p in self:
            if p.quantity > p.commitment.quantity:
                raise ValidationError(
                    'Assigned quantity higher than related commitment %s',
                    p.commitment.name)
            if p.quantity <= 0:
                raise ValidationError(
                    'Assigned quantity cannot be zero or negative')


class Event(models.Model):
    """add partial_event info on the event
    """
    _inherit = 'rea.event'

    fulfillment_partial_events = fields.One2many(
        'rea.fulfillment.event',
        'event',
        string="Partial events",
        help="Partial quantities used in a fulfillment relationship")
    fulfillment_balance = fields.Float(
        "Unfulfilling",
        compute='_fulfillment_balance',
        store=True,
        help="Amount not yet assigned to a commitment")

    @api.depends('fulfillment_partial_events', 'quantity')
    def _fulfillment_balance(self):
        for event in self:
            # check that the event is associated to a commitment
            assigned = sum(p.quantity for p in event.fulfillment_partial_events)
            event.fulfillment_balance = event.quantity - assigned

    def check_fulfillment(self):
        """check the validity of the fulfillment
        """
        pass


class Commitment(models.Model):
    """add partial_commitment info on the commitment
    """
    _inherit = 'rea.commitment'

    fulfillment_partial_commitments = fields.One2many(
        'rea.fulfillment.commitment',
        'commitment',
        string="Partial commitments",
        help="Partial quantities used in a fulfillment relationship")
    fulfillment_balance = fields.Float(
        "Unfulfilled",
        compute='_fulfillment_balance',
        store=True,
        help="Amount not yet assigned to an event")

    @api.depends('fulfillment_partial_commitments', 'quantity')
    def _fulfillment_balance(self):
        for commitment in self:
            # check that the commitment is associated to a commitment
            assigned = sum(p.quantity for p in commitment.fulfillment_partial_commitments)
            commitment.fulfillment_balance = commitment.quantity - assigned

    def fulfill(self, amount=None, ratio=None):
        """Create the full event if no args are given
        Otherwise create a partial event corresponding to the amount or ratio
        """
        for c in self:
            commitment = c.read(load=None)[0]
            event = {
                'name': commitment.get('name'),
                'type': None,  # FIXME
                'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'quantity': commitment.get('quantity'),  # FIXME
                'resource_type': commitment.get('resource_type'),
                'resource': commitment.get('resource'),
                'provider': commitment.get('provider'),
                'receiver': commitment.get('receiver'),
                'inflow': commitment.get('inflow'),
                'outflow': commitment.get('outflow'),
                'kind': commitment.get('kind'),
            }
            self.env['rea.event'].create(event)

    def check_fulfillment(self):
        """check the validity of the fulfillment
        """
        pass


class FulfillmentWizard(models.TransientModel):
    """Wizard used to link events to commitments
    with a fulfillment relationship
    Warning: the same model is used for both the object and the object lines
    """
    _name = 'rea.fulfillment.wizard'

    def _fulfillment_partial_events(self):
        model = self.env.context.get('active_model')
        if model != 'rea.event':
            return
        ids = self.env.context.get('active_ids')
        if not ids or self.env.context.get('norecs'):
            return []
        events = self.env[model].browse(ids)
        events.check_fulfillment()
        rec_ids = []
        for e in events:
            if e.fulfillment_balance <= 0:
                continue
            rec = self.with_context(
                {'norecs': True}
            ).create(
                {'event': e.id, 'quantity': e.fulfillment_balance})
            rec_ids.append(rec.id)
        if not rec_ids:
            raise UserError(u"Nothing to fulfill")
        return [(6, 0, rec_ids)]

    def _fulfillment_partial_commitments(self):
        model = self.env.context.get('active_model')
        if model != 'rea.commitment':
            return
        ids = self.env.context.get('active_ids')
        if not ids or self.env.context.get('norecs'):
            return []
        commitments = self.env[model].browse(ids)
        commitments.check_fulfillment()
        rec_ids = []
        for e in commitments:
            if e.fulfillment_balance <= 0:
                continue
            rec = self.with_context(
                {'norecs': True}
            ).create(
                {'commitment': e.id, 'quantity': e.fulfillment_balance})
            rec_ids.append(rec.id)
        if not rec_ids:
            raise UserError(u"Nothing to fulfill")
        return [(6, 0, rec_ids)]

    fulfillment_type = fields.Many2one(
        'rea.fulfillment.type')

    commitment = fields.Many2one(
        'rea.commitment',
        string="Commitment")
    commitment_provider = fields.Many2one(
        'rea.agent',
        related='commitment.provider',
        readonly=True)
    commitment_receiver = fields.Many2one(
        'rea.agent',
        related='commitment.receiver',
        readonly=True)
    commitment_resource_type = fields.Many2one(
        'rea.resource.type',
        related='commitment.resource_type',
        readonly=True,
        string="Resource Type")

    event = fields.Many2one(
        'rea.event',
        string="Event")
    event_provider = fields.Many2one(
        'rea.agent',
        related='event.provider',
        readonly=True)
    event_receiver = fields.Many2one(
        'rea.agent',
        related='event.receiver',
        readonly=True)
    event_resource_type = fields.Many2one(
        'rea.resource.type',
        related='event.resource_type',
        readonly=True,
        string="Resource Type")

    quantity = fields.Float(
        string="Quantity")

    event_fulfillment = fields.Many2one(
        'rea.fulfillment.wizard',
        string="Event Fulfillment")
    fulfillment_partial_events = fields.One2many(
        'rea.fulfillment.wizard',
        'event_fulfillment',
        default=_fulfillment_partial_events,
        string="Partial events")
    commitment_fulfillment = fields.Many2one(
        'rea.fulfillment.wizard',
        string="Commitment Fulfillment")
    fulfillment_partial_commitments = fields.One2many(
        'rea.fulfillment.wizard',
        'commitment_fulfillment',
        default=_fulfillment_partial_commitments,
        string="Partial commitments")

    def save_fulfillment(self):
        fulfillment = self.env['rea.fulfillment'].create(
            {'type': self.fulfillment_type.id})
        if not fulfillment.name:
            raise UserError(u"Please configure "
                            u"an automatic numbering for fulfillments")
        for p in self.fulfillment_partial_events:
            records = p.read(load='_classic_write')
            if len(records) != 1:
                raise UserError("Wizard bug, should not happen")
            record = records[0]
            record['fulfillment'] = fulfillment.id
            self.env['rea.fulfillment.event'].create(record)
        for p in self.fulfillment_partial_commitments:
            records = p.read(load='_classic_write')
            if len(records) != 1:
                raise UserError("Wizard bug, should not happen")
            record = records[0]
            record['fulfillment'] = fulfillment.id
            self.env['rea.fulfillment.commitment'].create(record)
        events = self.env['rea.event'].browse(
            [p.event.id for p in fulfillment.partial_events])
        events.check_fulfillment()
        commitments = self.env['rea.commitment'].browse(
            [p.commitment.id for p in fulfillment.partial_commitments])
        commitments.check_fulfillment()
