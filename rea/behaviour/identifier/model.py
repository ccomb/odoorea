from odoo import fields, models, api, osv
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTFORMAT
from datetime import datetime
from lxml import etree
import pytz


class IdentificationField(models.Model):
    """Setup for an identification field
    """
    _name = 'rea.identification.field'
    _description = "Setup for an Identification field"

    name = fields.Char(string="name", required=True, index=True)
    unique = fields.Boolean("Unique")
    mandatory = fields.Boolean("Mandatory")
    generated = fields.Boolean("Generated number")
    field_name = fields.Char(
        string="Field name")
    identification = fields.Many2one(
        'rea.identification',
        ondelete='cascade')
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
    model = fields.Many2one(
        'ir.model',
        string="Related model")
    field = fields.Many2one(
        'ir.model.fields',
        "Created field",
        required=True,
        ondelete='restrict')

    def _next_nb(self):
        for s in self:
            s.next_nb = s.last_nb + s.step

    def choose_next(self, dt):
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

    @api.model
    def create(self, vals):
        """ Create the real field when creating an identification field
        """
        field_name = vals.get('field_name')
        model = self.env.context.get('model')
        type_id = self.env.context.get('type_id')
        if not field_name or not model:
            raise Exception("Please create the field from the entity type")
        if field_name != 'name':
            field_name = 'x_ident_%s' % field_name
        vals['field_name'] = field_name
        fields = self.env['ir.model.fields']
        models = self.env['ir.model']
        entity_model = self.env[model]
        entity = entity_model.browse(type_id)
        model = model if entity.subtypes else model[:-5]
        model_id = models.search([('model', '=', model)])[0].id
        existing = fields.search([('model_id', '=', model_id),
                                  ('name', '=', field_name)])
        if existing:
            vals['field'] = existing[0].id
        else:
            if field_name != 'name':
                vals['field'] = fields.create({
                    'model': model,
                    'model_id': model_id,
                    'name': field_name,
                    'ttype': 'char'}).id
        vals['model'] = model_id
        if vals.get('unique'):
            entity_model._sql_constraints += [
                ('%s_uniq' % field_name,
                 'unique (%s)' % field_name,
                 "This %s already exists !" % vals.get('name', field_name))]
            entity_model._add_sql_constraints()
        return super(IdentificationField, self).create(vals)

    @api.multi
    def unlink(self):
        for vf in self:
            field = vf.field
            super(IdentificationField, self).unlink()
            # delete the concrete field if there are no remaining identfields
            if not self.search([('field_name', '=', field.name),
                                ('model', '=', field.model_id.id)]):
                # TODO prevent deleting existing data
                field.unlink()


class Identification(models.Model):
    _name = 'rea.identification'

    name = fields.Char(string="name", required=True, index=True)
    fields = fields.One2many(
        'rea.identification.field',
        'identification',
        string="Identification fields")

    @api.model
    def create(self, vals):
        """ Create by default the 'name' rea ident field
        """
        model = self.env.context.get('model')
        if not model:
            raise Exception("Please create the identification from the "
                            "identification tab of the entity type")
        models = self.env['ir.model']
        model_id = models.search([('model', '=', model)])[0].id
        identification = super(Identification, self).create(vals)
        field_id = self.env['ir.model.fields'].search([
            ('name', '=', 'name'), ('model_id', '=', model_id)])
        self.fields.create({
            'model': model_id, 'field': field_id, 'name': 'Name',
            'field_name': 'name', 'identification': identification.id})
        return identification


class IdentifiableType(models.AbstractModel):
    """ field to choose the identification fields on the entity type
    """
    _name = 'rea.identifiable.type'

    identification = fields.Many2one(
        'rea.identification',
        "Identification")


class Identifiable(models.AbstractModel):
    """ entity with configurable identifiers
    """
    _name = 'rea.identifiable.entity'
    _description = 'Identifiable entity'

    @api.depends('type')
    def _get_identification(self):
        for obj in self:
            obj.type_identification = obj.type.identification.id

    type_identification = fields.Many2one(
        'rea.identification',
        compute=_get_identification)

    def update_vals(self, vals):
        """update the vals dict with generated fields
        """
        if vals.get('type'):
            fields = self.type.browse(vals.get('type')).identification.fields
        elif self.type.identification.fields:
            fields = self.type.identification.fields
        else:
            return
        for field in fields:
            if not field.generated:
                continue
            date_origin = field.date_origin
            date_field = field.date_field
            now = datetime.now(
                pytz.timezone(self.env.context.get('tz') or 'UTC'))
            dt = now
            if date_origin is 'field':
                if not date_field:
                    raise UserError(
                        u'Missing Date Field in Identifier Setup "{}"'
                        .format(field.name))
                if vals.get(date_field):
                    dt = datetime.strptime(vals.get(date_field), DTFORMAT)
            if field.field_name:
                if not vals.get(field.field_name):
                    vals[field.field_name] = field.choose_next(dt)
                else:
                    pass

    @api.model
    def create(self, vals):
        self.update_vals(vals)
        return super(Identifiable, self).create(vals)

    def copy_data(self, default=None):
        vals = {}
        self.update_vals(vals)
        return super(Identifiable, self).copy_data(default=vals)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ Add identification fields
        """
        fvg = super(Identifiable, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        params = self.env.context.get('params')
        if not params or view_type != 'form':
            return fvg
        doc = etree.fromstring(fvg['arch'])
        group = doc.xpath("//page[@string='Identifiers']/group")[0]
        entity_model = params.get('model', self._name)
        type_model = entity_model + (
            '' if entity_model.endswith('.type') else '.type')
        type_table = self.env[type_model]._table
        self.env.cr.execute('''
            select distinct field.id
            from rea_identification_field field, %s type
            where field.identification = type.identification''' % type_table)
        field_ids = [t[0] for t in self.env.cr.fetchall()]
        fields = self.env['rea.identification.field'].browse(field_ids)
        for field in fields:
            if field.field_name == 'name':
                xmlfield = doc.xpath("//field[@name='name']")[0]
                osv.orm.transfer_modifiers_to_node(
                    {'readonly': field.generated},
                    xmlfield)
            elif field.field_name in self.env[entity_model]._fields:
                xmlfield = etree.Element(
                    'field',
                    name=field.field_name,
                    string=field.name)
                group.append(xmlfield)
                description = self.env[entity_model]._fields[
                    field.field_name].get_description(self.env)
                fvg['fields'][field.field_name] = description
                ident_id = field.identification.id
                osv.orm.transfer_modifiers_to_node(
                    {'invisible': [
                      ('type_identification', '!=', ident_id)],
                     'readonly': field.generated,
                     'required': (field.mandatory and
                                  [('type_identification', '=', ident_id)])},
                    xmlfield)
            else:
                pass
        fvg['arch'] = etree.tostring(doc)
        return fvg
