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
    _inherit = ['rea.identifiable.type',
                'rea.lifecycleable.type',
                'rea.propertyable.type',
                'rea.lifecycleable.entity',
                'rea.identifiable.entity',
                'rea.propertyable.entity']

    def name_get(self):
        result = []
        for r in self:
            result.append(
                (r.id, u"%s %s" % (r.uom.name or '', r.name)))
        return result

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
