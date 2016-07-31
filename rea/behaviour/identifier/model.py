from openerp import fields, models


class IdentifierSetup(models.Model):
    """Allows to create a configuration for identifiers
    """
    _name = 'rea.ident.setup'
    _description = "Identifier Setup"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    autonumber = fields.Boolean(
        'Autonumber')
    unique = fields.Boolean(
        'Unique')
    mandatory = fields.Boolean(
        'Mandatory')


class Identifier(models.Model):
    """ Identifiers (ex: SSN)
    """
    _name = 'rea.ident'
    _description = 'Identifiers'

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    setup = fields.Many2one(
        'rea.ident.setup',
        string="Setup")
