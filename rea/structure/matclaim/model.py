from odoo import fields, models, api, tools
from odoo.exceptions import ValidationError, UserError


class MaterializedClaimType(models.Model):
    """Abstract definition of a materialized claim.
    """
    _name = 'rea.matclaim.type'
    _description = 'Materialized Claim Type'
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
        'rea.matclaim.type',
        string="Materialized Claim Type")
    subtypes = fields.One2many(
        'rea.matclaim.type',
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

    _sql_contraints = [
        ('unique_matclaim_type_code', 'unique(code)',
         'Another materialized claim type with the same code already exists.'),
    ]


class MaterializedClaimGroup(models.Model):
    """ Group of materialized claims
    """
    _name = 'rea.matclaim.group'
    _description = "Materialized Claim Group"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    groups = fields.Many2one(
        'rea.matclaim.group',
        string="Group")


class MaterializedClaim(models.Model):
    """ Set of partial events gathered in a materialized claim.
    """
    _name = 'rea.matclaim'
    _description = 'Materialized Claim'
    _inherit = ['rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

    name = fields.Char(
        string="Name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.matclaim.type',
        string="Materialized Claim Type")
    partial_events = fields.One2many(
        'rea.matclaim.event',
        'matclaim',
        string="Partial events")

    def unlink(self):
        for d in self:
            events = [p.event for p in d.partial_events]
            super(MaterializedClaim, d).unlink()
            for event in events:
                # force recompute as it is not triggered
                event.write(
                    {'matclaim_balance':
                        event.quantity - sum(
                         p.quantity for p in event.matclaim_partial_events)})

    _sql_contraints = [
        ('unique_matclaim_name', 'unique(name)',
         'Another materialized claim with the same name already exists.'),
    ]


class PartialEvent(models.Model):
    """Partial event used in the materialized claim
    """
    _name = 'rea.matclaim.event'
    _description = "Partial Event for Materialized Claims"

    matclaim = fields.Many2one(
        'rea.matclaim',
        ondelete='cascade')
    event_type = fields.Many2one(
        'rea.event.type',
        related='event.type',
        readonly=True,
        string="Event type")
    event = fields.Many2one(
        'rea.event',
        required=True,
        string="Event")
    provider = fields.Many2one(
        'rea.agent',
        related='event.provider',
        readonly=True,
        string="Provider")
    quantity = fields.Float(
        required=True,
        string="Quantity")
    resource_type = fields.Many2one(
        'rea.resource.type',
        related='event.resource_type',
        readonly=True,
        string="Resource Type")
    receiver = fields.Many2one(
        'rea.agent',
        related='event.receiver',
        readonly=True,
        string="Receiver")

    def unlink(self):
        for p in self:
            matclaim = p.matclaim
            super(PartialEvent, p).unlink()
            if len(matclaim.partial_events) == 0:
                matclaim.unlink()
            events = self.env['rea.event'].browse(
                [p.event.id for p in matclaim.partial_events])
            events.check_matclaim()

    @api.onchange('event')
    def onchange_event(self):
        for p in self:
            p.quantity = p.event.matclaim_balance

    @api.constrains('quantity')
    def constrain_quantity(self):
        for p in self:
            if p.quantity > p.event.quantity:
                raise ValidationError(
                    'Claimed quantity higher than related event %s',
                    p.event.name)
            if p.quantity < 0:
                raise ValidationError(
                    'Claimed quantity cannot be negative')


class Event(models.Model):
    """add partial_event info on the event
    """
    _inherit = 'rea.event'

    matclaim_partial_events = fields.One2many(
        'rea.matclaim.event',
        'event',
        string="Partial events",
        help="Partial quantities gathered in a materialized claim")
    matclaim_balance = fields.Float(
        "Unclaimed",
        compute='_matclaim_balance',
        store=True)

    @api.depends('matclaim_partial_events', 'quantity')
    def _matclaim_balance(self):
        for event in self:
            claimed = sum(p.quantity for p in event.matclaim_partial_events)
            event.matclaim_balance = event.quantity - claimed

    def check_matclaim(self):
        """check the validity of the materialized claim
        """
        pass


class MaterializedClaimWizard(models.TransientModel):
    """Wizard used to gather events in a materialized claim
    """
    _name = 'rea.matclaim.wizard'

    def _matclaim_partial_events(self):
        ids = self.env.context.get('active_ids')
        if not ids or self.env.context.get('norecs'):
            return []
        events = self.env['rea.event'].browse(ids)
        events.check_matclaim()
        rec_ids = []
        for e in events:
            if e.matclaim_balance < 0:
                continue
            rec = self.with_context(
                {'norecs': True}
            ).create(
                {'event': e.id, 'quantity': e.matclaim_balance})
            rec_ids.append(rec.id)
        if not rec_ids:
            raise UserError(u"Nothing to claim")
        return [(6, 0, rec_ids)]

    mode = fields.Selection(
        [('create', "Create a new materialized claim"),
         ('add', "Add to an existing materialized claim")],
        default='create')
    matclaim_type = fields.Many2one(
        'rea.matclaim.type')
    matclaim = fields.Many2one(
        'rea.matclaim',
        string="Materialized Claim")
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

    wizard = fields.Many2one(
        'rea.matclaim.wizard',
        string="Materialized Claim")
    matclaim_partial_events = fields.One2many(
        'rea.matclaim.wizard',
        'wizard',
        default=_matclaim_partial_events,
        string="Partial events")

    def save_matclaim(self):
        if self.mode == 'create':
            matclaim = self.env['rea.matclaim'].create(
                {'type': self.matclaim_type.id})
        elif self.mode == 'add':
            matclaim = self.matclaim
        else:
            raise UserError('Wizard error: no mode specified')
        if not matclaim.name:
            raise UserError(u"Please configure "
                            u"an automatic numbering for materialized claims")
        for p in self.matclaim_partial_events:
            records = p.read(load='_classic_write')
            if len(records) != 1:
                raise UserError("Wizard bug, should not happen")
            record = records[0]
            record['matclaim'] = matclaim.id
            self.env['rea.matclaim.event'].create(record)
        events = self.env['rea.event'].browse(
            [p.event.id for p in matclaim.partial_events])
        events.check_matclaim()
