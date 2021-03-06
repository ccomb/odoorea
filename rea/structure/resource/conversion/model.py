# encoding: utf-8
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
        'rea.resource.conversion.type',
        required=True)
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

    _sql_contraints = [
        ('unique_resource_type_conversion', 'unique(type, from_restype)',
         'You can create only one conversion of a resource type'),
        ('unique_resource_conversion', 'unique(type, from_res)',
         'You can create only one conversion of a resource')
    ]

    def name_get(self):
        result = []
        for c in self:
            result.append(
                (c.id, u"%s: %s (%s)"
                 % (c.from_restype.name or c.from_res.name,
                    c.type.name,
                    c.to_restype.name or c.to_res.name)))
        return result

    @api.constrains('from_restype', 'from_res', 'to_restype', 'to_res')
    @api.one
    def _check_from(self):
        if (self.from_restype and self.from_res
           or self.to_restype and self.to_res):
            raise ValidationError(
                _("You cannot specify both a resource and a resource type"))

    def convert(self, conversion_type, resource_type):
        """Convert the resource type using the conversion table
        """
        # TODO add a convert with a date range or other condition
        c = self.search([('type', '=', conversion_type.id),
                         ('from_restype', '=', resource_type.id)])
        return c[0].to_qty / c[0].from_qty if c else 0
