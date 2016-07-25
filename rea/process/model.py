from openerp import fields, models


class Process(models.Model):
    """ Set of events bound by a duality relationship.
    """
    _name = 'rea.process'
    _description = 'Process'

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.process.type',
        string="Process Type")
    events = fields.Many2many(
        'rea.event',
        string="Events")


class ProcessType(models.Model):
    """ Set of event types bound by a duality relationship.
    Abstract definition of actual Processes
    """
    _name = 'rea.process.type'
    _description = 'Process Type'

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    kind = fields.Selection([
        ('exchange', "Exchange"),
        ('conversion', "Conversion")],
        string="Kind")
    event_types = fields.Many2many(
        'rea.event.type',
        string="Event Types")
