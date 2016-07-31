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
    process = fields.Many2one(
        'rea.process',
        string="Process",
        help="The process this event is part of")

    def create(self):
        """ During the create we run the hooks of the aspects that modify the
        features corresponding to the exchange or conversion.
        For example an 'owner' property during an exchange process"""
        # TODO
        return super(Event, self).create()


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
        [('increment', 'Increment'),
         ('decrement', 'Decrement')],
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


class EventGroup(models.Model):
    """ Group of events
    """
    _name = 'rea.event.group'
    _description = "Event Group"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    groups = fields.Many2one(
        'rea.event.group',
        string="Group")
