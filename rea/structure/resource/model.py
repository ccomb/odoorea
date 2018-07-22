from odoo import fields, models, tools


class Resource(models.Model):
    """ Something scarce and of economic interest for Agents.
    It is exchanged, produced or consumed during economic Events
    """
    _name = 'rea.resource'
    _description = "Resource"
    _inherit = ['rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

    name = fields.Char(
        string="Name",
        required=True,
        index=True)
    quantity = fields.Float(
        'Quantity',
        default=1,
        help=u"The quantity of the specified type")
    type = fields.Many2one(
        'rea.resource.type',
        string="Type",
        ondelete='restrict')
    groups = fields.Many2many(
        'rea.resource.group',
        string="Groups")
    reserved = fields.Many2many(
        'rea.commitment',
        string=u"Reserved by")
    conversions = fields.One2many(
        'rea.resource.conversion',
        'from_res',
        "Conversions")

    _sql_contraints = [
        ('unique_resource_name', 'unique(name)',
         'Another resource with the same name already exists.'),
    ]

    def name_get(self):
        result = []
        for r in self:
            result.append(
                (r.id, u"%s %s %s"
                       % (r.quantity or '', r.type.name or '', r.name)))
        return result


class ResourceType(models.Model):
    """ Abstract definition of actual resources
    """
    _name = 'rea.resource.type'
    _description = "Resource Type"
    _parent_name = 'type'
    _inherit = ['rea.type.identifier',
                'rea.type.lifecycle',
                'rea.type.property',
                'rea.entity.lifecycle',
                'rea.entity.identifier',
                'rea.entity.property']
    tools.generate_views(__file__, _name, _inherit)

    def name_get(self):
        result = []
        for r in self:
            result.append(
                (r.id, u"%s %s" % (r.uom.name or '', r.name)))
        return result

    name = fields.Char(
        string="Name",
        required=True,
        index=True)
    code = fields.Char(
        string="Code",
        required=True,
        help=u"arbitrary technical code",
        index=True)
    type = fields.Many2one(
        'rea.resource.type',
        string="Type",
        ondelete='restrict')
    subtypes = fields.One2many(
        'rea.resource.type',
        'type',
        copy=True,
        string="Sub-types")
    structural = fields.Boolean(
        'Structural type?',
        help="Hide in operational choices?")
    max_reservations = fields.Integer(
        u"Max reservations",
        default=1)
    groups = fields.Many2many(
        'rea.resource.group',
        string="Groups")
    uom = fields.Many2one(
        'rea.uom',
        )
    # TODO recursive with parent?
    conversions = fields.One2many(
        'rea.resource.conversion',
        'from_restype',
        "Conversions")

    _sql_contraints = [
        ('unique_resource_type_code', 'unique(code)',
         'Another resource type with the same code already exists.'),
    ]


class ResourceGroup(models.Model):
    """ Group of resources
    """
    _name = 'rea.resource.group'
    _description = "Resource Group"

    name = fields.Char(
        string="Name",
        required=True,
        index=True)
    code = fields.Char(
        string="code",
        index=True)
    group = fields.Many2one(
        'rea.resource.group',
        string="Group")
