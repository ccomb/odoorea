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


class ResourceType(models.Model):
    """ Abstract definition of actual resources
    """
    _name = 'rea.resource.type'
    _description = "Resource Type"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    # TODO recursive with parent?
