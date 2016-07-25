from openerp import fields, models


class Event(models.Model):
    """ Exchange or conversion of economic Resources by economic Agents
    """
    _name = 'rea.event'
    _description = "Event"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.event.type',
        string="Type")
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


class EventType(models.Model):
    """ Abstract definition of actual events
    """
    _name = 'rea.event.type'
    _description = "Event Type"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    kind = fields.Selection(
        [('i', 'Increment'),
         ('d', 'Decrement')],
        string="Kind")
    provider = fields.Many2one(
        'rea.agent.type',
        string="Provider Type")
    receiver = fields.Many2one(
        'rea.agent.type',
        string="Receiver Type")
    resource_type = fields.Many2one(
        'rea.resource.type',
        string="Resource Type")
