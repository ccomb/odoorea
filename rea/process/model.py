from openerp import fields, models


class Process(models.Model):
    """ Set of event types bound by a duality reliationship
    """
    _name = 'rea.process'
    _description = 'Process'

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    event_types = fields.Many2many(
        'rea.event.type',
        string="Event Types")
    kind = fields.Selection([
        ('exchange', "Exchange"),
        ('conversion', "Conversion")],
        string="Kind")

#  to be consistent with other models we could have a 'type' attribute
#  pointing to a ProcessType, itself having a kind attribute.
