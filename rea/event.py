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
    provider = fields.Many2one(
        'rea.agent',
        string="Provider")
    receiver = fields.Many2one(
        'rea.agent',
        string="Receiver")


class EventType(models.Model):
    """ Abstract definition of actual events
    """
    _name = 'rea.event.type'
    _description = "Event Type"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Selection([
        ('i', 'Increment'),
        ('d', 'Decrement')])
