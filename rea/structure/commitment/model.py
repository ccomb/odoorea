from openerp import fields, models
from odoo import api


class Commitment(models.Model):
    """ Promise of economic Event at a future or unknown date
    """
    _name = 'rea.commitment'
    _description = "Commitment"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.commitment.type',
        domain="[('contract_type', '=', contract_type)]",
        string="Type")
    groups = fields.Many2many(
        'rea.commitment.group',
        string="Groups")
    date = fields.Date(
        "Expected date")
    events = fields.Many2many(
        'rea.event',
        string="Events",
        help="Events fulfilling this commitment")
    quantity = fields.Float(
        string="Quantity")
    resource_type = fields.Many2one(
        'rea.resource.type',
        string="Resource Type")
    provider = fields.Many2one(
        'rea.agent',
        string="Provider")
    contract = fields.Many2one(
        'rea.contract',
        string="Contract")
    contract_type = fields.Many2one(
        'rea.contract.type',
        compute='_contract_type')
    receiver = fields.Many2one(
        'rea.agent',
        string="Receiver")

    @api.depends('contract')
    def _contract_type(self):
        for commitment in self:
            commitment.contract_type = commitment.contract.type

    def fulfill(self):
        """Create the event
        """
        raise NotImplementedError


class CommitmentType(models.Model):
    """ Astract definition of actual commitments
    """
    _name = 'rea.commitment.type'
    _description = "Commitment Type"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    kind = fields.Selection([
        ('increment', 'Increment'),
        ('decrement', 'Decrement')],
        string="Kind")
    contract_type = fields.Many2one(
        'rea.contract.type',
        string="Contract Type")


class CommitmentGroup(models.Model):
    """ Group of commitments
    """
    _name = 'rea.commitment.group'
    _description = "Commitment Group"

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    groups = fields.Many2one(
        'rea.commitment.group',
        string="Group")
