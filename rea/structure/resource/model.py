from odoo import fields, models


class Resource(models.Model):
    """ Something scarce and of economic interest for Agents.
    It is exchanged, produced or consumed during economic Events
    """
    _name = 'rea.resource'
    _description = "Resource"
    _inherit = ['rea.lifecycleable.entity',
                'rea.identifiable.entity',
                'rea.propertyable.entity']

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    quantity = fields.Float(
        'Quantity',
        default=1,
        help=u"The quantity of the specified type")
    type = fields.Many2one(
        'rea.resource.type',
        string="Type")
    groups = fields.Many2many(
        'rea.resource.group',
        string="Groups")
    reserved = fields.Many2many(
        'rea.commitment',
        string=u"Reserved by")


class ResourceType(models.Model):
    """ Abstract definition of actual resources
    """
    _name = 'rea.resource.type'
    _description = "Resource Type"
    _parent_name = 'type'
    _inherit = ['rea.identifiable.type',
                'rea.lifecycleable.type',
                'rea.propertyable.type',
                'rea.lifecycleable.entity',
                'rea.identifiable.entity',
                'rea.propertyable.entity']

    type = fields.Many2one(
        'rea.resource.type',
        string="Type")
    subtypes = fields.One2many(
        'rea.resource.type',
        'type',
        copy=True,
        string="Sub-types")
    structural = fields.Boolean(
        'Structural type?',
        help="Hide in operational choices?")
    name = fields.Char(
        string="name",
        required=True,
        index=True)
    max_reservations = fields.Integer(
        u"Max reservations",
        default=1)
    groups = fields.Many2many(
        'rea.resource.group',
        string="Groups")
    quantity = fields.Float(
        'Quantity',
        default=1,
        help=u"The unit quantity corresponding to this resource type."
             u"Used for conversions")
    uom = fields.Many2one(
        'rea.uom',
        )
    # TODO recursive with parent?


class ResourceGroup(models.Model):
    """ Group of resources
    """
    _name = 'rea.resource.group'
    _description = "Resource Group"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    code = fields.Char(
        string="code",
        index=True)
    group = fields.Many2one(
        'rea.resource.group',
        string="Group")


class ConversionType(models.Model):
    """ Type of a conversion between resource types
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
    from_uom = fields.Many2one(
        'rea.uom',
        string="Unit")
    from_restype = fields.Many2one(
        'rea.resource.type',
        string="Resource Type")
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
    to_uom = fields.Many2one(
        'rea.uom',
        string="Unit")
    to_restype = fields.Many2one(
        'rea.resource.type',
        string="Resource Type")
