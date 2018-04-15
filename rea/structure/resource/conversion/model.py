from odoo import fields, models


class ConversionType(models.Model):
    """ Type of a value between resource types
    public price, retailer price, exchange rate, etc.
    """
    _name = 'rea.conversion.type'
    _description = "Conversion Type"

    name = fields.Char("Name")


class Conversion(models.Model):
    """ Conversion between two resource types with their uom
    """
    _name = 'rea.conversion'
    _description = "Conversion Table for Units and resource_types"

    type = fields.Many2one(
        'rea.conversion.type')
    from_qty = fields.Float("Quantity")
    from_restype = fields.Many2one(
        'rea.resource.type',
        string="Resource Type")
    kind = fields.Selection([
        ('konst', 'Constant'),
        ('calc', 'Calculation')],
        default='konst')
    date_start = fields.Datetime("From")
    date_end = fields.Datetime("To")
    observables = fields.Many2many(
        'rea.observable',
        string="Observables")
    expression = fields.Char(
        "Expression",
        help=("Python expression"))
    resolution = fields.Float(
        "Period",
        help=u"Recompute the value at every period of time")
    next_valuation = fields.Datetime(
        "Next valuation date")  # TODO also add a last_valuation
    to_qty = fields.Float("Quantity")
    to_restype = fields.Many2one(
        'rea.resource.type',
        string="Resource Type")
