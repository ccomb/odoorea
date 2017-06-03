from odoo import fields, models, api
from odoo.exceptions import ValidationError


class EventDuality(models.Model):
    """Reconciliation between two Events
    Events should be in opposite directions
    (one increment and one decrement)
    """
    _name = 'rea.event.duality'
    _description = "Event Duality"

    initiator = fields.Many2one(
        'rea.event',
        string="Initiator Event")
    initiator_quantity = fields.Float(
        required=True,
        string="Quantity")
    initiator_resource_type = fields.Many2one(
        'rea.resource.type',
        related='initiator.resource_type',
        readonly=True,
        string="Resource Type")
    terminator = fields.Many2one(
        'rea.event',
        required=True,
        string="Terminator Event")
    terminator_quantity = fields.Float(
        required=True,
        string="Quantity")
    terminator_resource_type = fields.Many2one(
        'rea.resource.type',
        related='terminator.resource_type',
        readonly=True,
        string="Resource Type")

    @api.onchange('initiator')
    def onchange_initiator(self):
        for d in self:
            d.initiator_quantity = d.initiator.quantity

    @api.onchange('terminator')
    def onchange_terminator(self):
        for d in self:
            d.terminator_quantity = d.terminator.quantity

    @api.constrains('initiator_quantity', 'terminator_quantity')
    def constrain_quantity(self):
        for duality in self:
            if duality.initiator_quantity > duality.initiator.quantity:
                raise ValidationError(
                    'Assigned quantity higher than related event %s',
                    duality.initiator.name)
            if duality.terminator_quantity > duality.terminator.quantity:
                raise ValidationError(
                    'Assigned quantity higher than related event %s',
                    duality.terminator.name)
            if duality.initiator_quantity <= 0:
                raise ValidationError(
                    'Assigned quantity cannot be zero or negative')
            if duality.terminator_quantity <= 0:
                raise ValidationError(
                    'Assigned quantity cannot be zero or negative')


class Event(models.Model):
    """add duality info on the event
    """
    _inherit = 'rea.event'

    initiators = fields.One2many(
        'rea.event.duality',
        'terminator',
        string="Initiators",
        help="Other events reconciled with the current event")
    terminators = fields.One2many(
        'rea.event.duality',
        'initiator',
        string="Terminators",
        help="Other events that reconcile the current event")
    is_reconciled = fields.Boolean(
        "Reconciled",
        compute='_is_reconciled',
        store=True)

    @api.depends('initiators', 'terminators')
    def _is_reconciled(self):
        for event in self:
            # check that the initiator event is reconciled
            sum_t = sum(i.terminator_quantity for i in event.initiators)
            sum_i = sum(t.initiator_quantity for t in event.terminators)
            if sum_i + sum_t == event.quantity:
                event.is_reconciled = True
            else:
                event.is_reconciled = False
