from openerp import fields, models


class Resource(models.Model):
    """ Something scarce and of economic interest for Agents.
    It is exchanged, produced or consumed during economic Events
    """
    _name = 'rea.resource'
    _description = "Resource"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
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

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    max_reservations = fields.Integer(
        u"Max reservations",
        default=1)
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
    group = fields.Many2one(
        'rea.resource.group',
        string="Group")
