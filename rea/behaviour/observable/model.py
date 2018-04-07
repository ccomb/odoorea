from odoo import fields, models
import pint
ureg = pint.UnitRegistry()


class Observable(models.Model):
    _name = 'rea.observable'
    _description = "Observable for calculations"

    name = fields.Char("Name")
    sequence = fields.Integer("Sequence")
    type = fields.Selection([
        ('konst', 'Constant'),
        ('days', 'Days after'),
        ('time', 'Current Time'),
        ('field', 'Entity field')])
    konst = fields.Float("Value")
    date = fields.Date("Date")
    field = fields.Many2one(
        'ir.model.fields',
        string="Dependent field",
        help="Used as a variable name in the expression")

    def value(self, entity):
        """ get the value of the observable
        """
        if self.type == 'konst':
            return self.konst
        if self.type == 'field' and self.field:
            magnitude = getattr(entity, self.field.name)
            unitfieldname = 'x_unit_%s' % self.field.name[2:]
            if hasattr(entity, unitfieldname):
                unit = ureg.parse_units(getattr(entity, unitfieldname).name)
            return magnitude * unit
        raise NotImplementedError
