from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFORMAT
from datetime import datetime
import pytz


class TemplatePlugin():
    """Allows to create a configuration for identifiers
    """


class IdentSequenceSetup(models.Model):
    """Setup for an identifier type (ex: SSN numbering)
    """
    _name = 'rea.ident.sequence.setup'
    _description = "Identifier Sequence Setup"

    name = fields.Char(string="name", required=True, index=True)
    field = fields.Char(string="Field")
    plugin = fields.Selection([
        ('templated_sequence', "Templated sequence"),
    ])
    template = fields.Char("Template String", help="TODO")
    last_id = fields.Integer('Last id')
    prefix = fields.Char('Prefix')
    suffix = fields.Char('Suffix')
    last_nb = fields.Integer('Last nb', default=0)
    next_nb = fields.Integer('Next nb', compute="_next_nb")
    padding = fields.Integer('Padding', default=5)
    step = fields.Integer('Step', default=1)
    date_origin = fields.Selection([
        ('now', 'Current date'),
        ('field', 'Date field')],
        string="Date to use",
        default='now')
    date_field = fields.Char("Date field")

    def _next_nb(self):
        for s in self:
            s.next_nb = s.last_nb + s.step

    def name_choose(self, dt):
        """ Generate the next identifier value,
        possibly using the provided datetime dt
        """
        self.env.cr.execute(
            "SELECT last_nb FROM {} WHERE id=%s FOR UPDATE NOWAIT"
            .format(self._table),
            [self.id])
        last_nb = self.env.cr.fetchone()[0]
        next_nb = last_nb + self.step
        self.env.cr.execute(
            "UPDATE {} SET last_nb=%s WHERE id=%s "
            .format(self._table),
            (next_nb, self.id))
        self.invalidate_cache(['last_nb'], [self.id])
        return '{prefix}{next_nb:0>{fill}}{suffix}'.format(
            prefix=datetime.strftime(dt, self.prefix or ''),
            next_nb=next_nb,
            fill=self.padding,
            suffix=datetime.strftime(dt, self.suffix or ''))

    def name_check(self, val):
        """ Check the value and return None or the validation error string
        """
        raise NotImplementedError


class IdentifierTypeSetup(models.AbstractModel):
    """ field to store the identifier setup
    """
    _name = 'rea.ident.sequence.store'
    ident_setup = fields.Many2one(
        'rea.ident.sequence.setup',
        string="Ident setup")


class SequenceIdentifier(models.AbstractModel):
    """ configurable Name identifier
    """
    _name = 'rea.ident.sequence'
    _description = 'Identification behaviour'

    @api.model
    def create(self, vals):
        ident_setup = self.type.browse(vals.get('type')).ident_setup
        if not ident_setup:
            return super(SequenceIdentifier, self).create(vals)
        date_origin = ident_setup.date_origin
        date_field = ident_setup.date_field
        now = datetime.now(pytz.timezone(self.env.context.get('tz') or 'UTC'))
        dt = now
        if date_origin is 'field':
            if not date_field:
                raise UserError(u'Missing Date Field in Identifier Setup "{}"'
                                .format(ident_setup.name))
            if vals.get(date_field):
                dt = datetime.strptime(vals.get(date_field), DTFORMAT)
        if ident_setup.field:
            if not vals.get(ident_setup.field):
                vals[ident_setup.field] = ident_setup.name_choose(dt)
            else:
                pass
        return super(SequenceIdentifier, self).create(vals)
