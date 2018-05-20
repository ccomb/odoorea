from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ConversionType(models.Model):
    """ Type of a value between resource types
    public price, retailer price, exchange rate, etc.
    """
    _name = 'rea.resource.conversion.type'
    _description = "Conversion Type"

    name = fields.Char("Name")


class Conversion(models.Model):
    """ Conversion between two resource or resource types
    with their uom
    """
    _name = 'rea.resource.conversion'
    _description = "Resource Conversion Table"

    type = fields.Many2one(
        'rea.resource.conversion.type')
    from_qty = fields.Float("Quantity")
    from_restype = fields.Many2one(
        'rea.resource.type',
        string="Resource Type")
    from_res = fields.Many2one(
        'rea.resource',
        string="Resource")
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
    to_res = fields.Many2one(
        'rea.resource',
        string="Resource")

    @api.constrains('from_restype', 'from_res', 'to_restype', 'to_res')
    @api.one
    def _check_from(self):
        if (self.from_restype and self.from_res
           or self.to_restype and self.to_res):
            raise ValidationError(
                _("You cannot specify both a resource and a resource type"))
