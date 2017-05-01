from odoo import fields, models, api, _


class Commitment(models.Model):
    """ Promise of economic Event at a future or unknown date
    """
    _name = 'rea.commitment'
    _description = "Commitment"
    _inherit = ['rea.ident.sequence']

    def _default_provider(self):
        for agent in self.contract.agents:
            if agent.type == self.type.provider_type:
                return agent

    def _default_receiver(self):
        for agent in self.contract.agents:
            if agent.type == self.type.receiver_type:
                return agent

    @api.onchange('type')
    def _change_receiver(self):
        for commitment in self:
            commitment.receiver = commitment._default_receiver()

    @api.onchange('type')
    def _change_provider(self):
        for commitment in self:
            commitment.provider = commitment._default_provider()

    name = fields.Char(
        string="name",
        required=True,
        default=lambda self: _('New'),
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
    contract = fields.Many2one(
        'rea.contract',
        string="Contract")
    contract_type = fields.Many2one(  # just for a domain
        'rea.contract.type',
        compute='_contract_type')
    provider = fields.Many2one(
        'rea.agent',
        default=_default_provider,
        string="Provider")
    receiver = fields.Many2one(
        'rea.agent',
        default=_default_receiver,
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
    _inherit = ['rea.ident.sequence.store']

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
    provider_type = fields.Many2one(
        'rea.agent.type',
        string="Provider Type")
    receiver_type = fields.Many2one(
        'rea.agent.type',
        string="Receiver Receiver")


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
