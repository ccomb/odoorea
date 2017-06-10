from openerp import fields, models


class Process(models.Model):  # TODO ProcessInstance?
    """ Set of partial events bound by a duality relationship.
    (partial events are reconciliations)
    This can be compared to an enhanced letter of reconciliation
    """
    _name = 'rea.process'
    _description = 'Process'
    _inherit = ['rea.ident.sequence']

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    type = fields.Many2one(
        'rea.process.type',
        string="Process Type")
    reconciliations = fields.One2many(
        'rea.event.reconciliation',
        'process',
        string="Reconciliations")

    def unlink(self):
        for p in self:
            events = [r.event for r in p.reconciliations]
            super(Process, p).unlink()
            for event in events:
                # force recompute as it is not triggered
                event.write(
                    {'balance':
                        event.quantity - sum(r.quantity for r in event.reconciliations)})


class ProcessType(models.Model):
    """ Set of event types bound by a duality relationship.
    Abstract definition of actual Processes.
    It contains the rules of the process.
    """
    _name = 'rea.process.type'
    _description = 'Process Type'
    _inherit = ['rea.ident.sequence.store']

    name = fields.Char(
        string="name",
        required=True,
        index=True)
    kind = fields.Selection([
        ('exchange', "Exchange"),
        ('conversion', "Conversion")],
        string="Kind")
    event_types = fields.Many2many(
        'rea.event.type',
        string="Event Types")

    # for each processtype, create an action button to start a new process
