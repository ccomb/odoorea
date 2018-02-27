from odoo import fields, models, api
from odoo.exceptions import ValidationError, UserError


class Reconciliation(models.Model):
    """Reconciliation between two or more Events
    """
    _name = 'rea.event.reconciliation'
    _description = "Event Reconciliation"

    process = fields.Many2one(
        'rea.process',
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
        for r in self:
            process = r.process
            super(Reconciliation, r).unlink()
            if len(process.reconciliations) == 0:
                process.unlink()
            events = self.env['rea.event'].browse(
                [r.event.id for r in process.reconciliations])
            events.check_agents()

    @api.onchange('event')
    def onchange_event(self):
        for r in self:
            r.quantity = r.event.balance

    @api.constrains('quantity')
    def constrain_quantity(self):
        for r in self:
            if r.quantity > r.event.quantity:
                raise ValidationError(
                    'Assigned quantity higher than related event %s',
                    r.event.name)
            if r.quantity <= 0:
                raise ValidationError(
                    'Assigned quantity cannot be zero or negative')


class Event(models.Model):
    """add reconciliation info on the event
    """
    _inherit = 'rea.event'

    reconciliations = fields.One2many(
        'rea.event.reconciliation',
        'event',
        string="Reconciliations",
        help="Partial quantities reconciled and assigned to a process")
    balance = fields.Float(
        "Unreconciled",
        compute='_balance',
        store=True)

    @api.depends('reconciliations')
    def _balance(self):
        for event in self:
            # check that the event is reconciled
            assigned = sum(r.quantity for r in event.reconciliations)
            event.balance = event.quantity - assigned

    def check_agents(self):
        agents = {}
        for e in self:
            agents.setdefault(e.provider.id, {'r': 0, 'p': 0})
            agents.setdefault(e.receiver.id, {'r': 0, 'p': 0})
            agents[e.provider.id]['p'] += 1
            agents[e.receiver.id]['r'] += 1
        if any(any([i['r'] == 0, i['p'] == 0]) for i in agents.values()):
            raise ValidationError(
                u"Invalid reconciliation: "
                u"at least one agent is not both a receiver and a provider")
        if len(self) < 2:
            raise ValidationError(
                u"Invalid reconciliation: "
                u"two events or more should be selected")


class ReconcileWizard(models.TransientModel):
    """Wizard used to reconcile events
    """
    _name = 'rea.event.reconciliation.wizard'

    def _reconciliations(self):
        ids = self.env.context.get('active_ids')
        if not ids or self.env.context.get('norecs'):
            return []
        events = self.env['rea.event'].browse(ids)
        events.check_agents()
        rec_ids = []
        for e in events:
            if e.balance <= 0:
                continue
            rec = self.with_context(
                {'norecs': True}
            ).create(
                {'event': e.id, 'quantity': e.balance})
            rec_ids.append(rec.id)
        if not rec_ids:
            raise UserError(u"Nothing to reconcile")
        return [(6, 0, rec_ids)]

    process_type = fields.Many2one(
        'rea.process.type')
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

    reconciliation = fields.Many2one(
        'rea.event.reconciliation.wizard',
        string="Reconciliation")
    reconciliations = fields.One2many(
        'rea.event.reconciliation.wizard',
        'reconciliation',
        default=_reconciliations,
        string="Reconciliations")

    def save_reconciliation(self):
        process = self.env['rea.process'].create(
            {'type': self.process_type.id})
        if not process.name:
            raise UserError(u"Please configure "
                            u"an automatic numbering for processes")
        for r in self.reconciliations:
            records = r.read(load='_classic_write')
            if len(records) != 1:
                raise UserError("Wizard bug, shouldn't happen")
            record = records[0]
            record['process'] = process.id
            self.env['rea.event.reconciliation'].create(record)
        events = self.env['rea.event'].browse(
            [r.event.id for r in process.reconciliations])
        events.check_agents()
