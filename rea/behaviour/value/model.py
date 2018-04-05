from odoo import fields, models, api, osv
from lxml import etree
import time


class UnitOfMeasure(models.Model):
    """ Unit of measure of values
    """
    _name = 'rea.uom'
    _description = "Unit of measure"

    name = fields.Char(
        'Name')
    code = fields.Char(
        'Code')


class ValuationField(models.Model):
    """Setup for a valuation field
    """
    _name = 'rea.valuation.field'
    _description = "Setup for a Value field"

    name = fields.Char(string="name", required=True, index=True)
    mandatory = fields.Boolean("Mandatory")
    field_name = fields.Char(
        string="Field name")
    valuation = fields.Many2one(
        'rea.valuation',
        help=u"The valuation configuration this fiels belongs to",
        ondelete='cascade')
    field = fields.Many2one(
        'ir.model.fields',
        "Created field",
        required=True,
        ondelete='restrict')
    type = fields.Selection([
        ('konst', 'Constant'),
        ('calc', 'Calculation')])
    observables = fields.One2many(
        'rea.value.observable',
        'value_field',
        string="Observables")
    expression = fields.Char(
        "Expression",
        help=("Python expression"))
    resolution = fields.Float(
        "Period",
        help=u"Recompute the value at every period of time")
    next_valuation = fields.Datetime(
        "Next valuation date")  # TODO also add a last_valuation

    def compute_all(self):
        # TODO optimize
        for obj in ('rea_resource', 'rea_event', 'rea_agent',
                    'rea_commitment', 'rea_contract'):
            # compute entity types first...
            self.env.cr.execute(
                "select t1.id, f.id "
                "from %(obj)s_type t1, %(obj)s_type t2, "
                "     rea_valuation v, rea_valuation_field f "
                "where "
                "    t1.type = t2.id "
                "and f.type = 'calc' "
                "and t2.valuation = v.id "
                "and f.valuation = v.id "
                "and (f.next_valuation < '%(now)s' "
                "     or f.next_valuation is NULL)"
                % {'obj': obj, 'now': time.strftime('%Y-%m-%d %H:%M:%S')})
            for ent_type_id, field_id in self.env.cr.fetchall():
                field = self.env['rea.valuation.field'].browse(field_id)
                ent_type = self.env['%s.type' % obj.replace('_', '.')
                                    ].browse(ent_type_id)
                ent_type.write({field.field.name: field.compute(ent_type)})
            # ...then entities
            self.env.cr.execute(
                "select r.id, f.id "
                "from %(obj)s r, %(obj)s_type t, "
                "     rea_valuation v, rea_valuation_field f "
                "where "
                "    r.type = t.id "
                "and f.type = 'calc' "
                "and t.valuation = v.id "
                "and f.valuation = v.id "
                "and (f.next_valuation < '%(now)s' "
                "     or f.next_valuation is NULL)"
                % {'obj': obj, 'now': time.strftime('%Y-%m-%d %H:%M:%S')})
            for entity_id, field_id in self.env.cr.fetchall():
                field = self.env['rea.valuation.field'].browse(field_id)
                entity = self.env[obj.replace('_', '.')].browse(entity_id)
                entity.write({field.field.name: field.compute(entity)})

    def compute(self, entity):
        """given a calculation and an entity, return the new value of the field
        """
        for vfield in self:
            localvars = {o.name: o.value(entity) for o in vfield.observables}
            # TODO memoize and use a resolution (day, minute, etc.)
            # to avoid recreating the commitment at each term execution
            # FIXME unsafe
            if self.expression is False:
                continue
            value = eval(self.expression,
                         {"__builtins__": {}},
                         localvars)
            return value
            # _function(time.strftime('%Y-%m-%d %H:%M:%S'))

    @api.model
    def create(self, vals):
        """ Create the real field when creating a value field
        Also create the unit field (resource_type)
        """
        field_name = vals.get('field_name')
        model = self.env.context.get('model')
        type_id = self.env.context.get('type_id')
        if not field_name or not model:
            raise Exception("Please create the field from the entity type")
        if field_name != 'name':
            field_name = 'x_value_%s' % field_name
        vals['field_name'] = field_name
        fields = self.env['ir.model.fields']
        models = self.env['ir.model']
        entity_model = self.env[model]
        entity = entity_model.browse(type_id)
        model = model if entity.subtypes else model[:-5]
        model_id = models.search([('model', '=', model)])[0].id
        existing = fields.search([('model_id', '=', model_id),
                                  ('name', '=', field_name)])
        rt_field_name = 'x_valueunit_%s' % field_name[8:]
        if existing:
            vals['field'] = existing[0].id
        else:
            if field_name != 'name':
                # value
                vals['field'] = fields.create({
                    'model': model,
                    'model_id': model_id,
                    'name': field_name,
                    'field_description': vals.get('name'),
                    'ttype': 'float'}).id
                # unit (resource type)
                fields.create({
                    'model': model,
                    'model_id': model_id,
                    'name': rt_field_name,
                    'field_description': '%s Unit' % vals.get('name'),
                    'ttype': 'many2one',
                    'relation': 'rea.resource.type'}).id
        vals['model'] = model_id
        return super(ValuationField, self).create(vals)

    @api.multi
    def unlink(self):
        for vf in self:
            field = vf.field
            super(ValuationField, self).unlink()
            # TODO prevent deleting existing data
            # delete the concrete field if there are no remaining identfields
            if not self.search([('field_name', '=', field.name),
                                ('model', '=', field.model_id.id)]):
                field.search([('model', '=', field.model),
                              ('name', '=', 'x_valueunit_' + field.name[8:])]
                             ).unlink()
                field.unlink()


class Valuation(models.Model):
    _name = 'rea.valuation'

    name = fields.Char(string="name", required=True, index=True)
    fields = fields.One2many(
        'rea.valuation.field',
        'valuation',
        string="Value fields")


class ValuableType(models.AbstractModel):
    """ field to choose the value fields on the entity type
    """
    _name = 'rea.valuable.type'

    valuation = fields.Many2one(
        'rea.valuation',
        "Valuation")


class Valuable(models.AbstractModel):
    """ entity with configurable values
    """
    _name = 'rea.valuable.entity'
    _description = 'Valuable entity'

    @api.depends('type')
    def _get_valuation(self):
        for obj in self:
            obj.type_valuation = obj.type.valuation.id

    type_valuation = fields.Many2one(
        'rea.valuation',
        compute=_get_valuation)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ Add value fields
        """
        fvg = super(Valuable, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        params = self.env.context.get('params')
        if not params or view_type != 'form':
            return fvg
        doc = etree.fromstring(fvg['arch'])
        group = doc.xpath("//page[@string='Values']/group/group")[0]
        entity_model = params.get('model', self._name)
        type_model = entity_model + (
            '' if entity_model.endswith('.type') else '.type')
        type_table = self.env[type_model]._table
        self.env.cr.execute('''
            select distinct field.id
            from rea_valuation_field field, %s type
            where field.valuation = type.valuation''' % type_table)
        field_ids = [t[0] for t in self.env.cr.fetchall()]
        fields = self.env['rea.valuation.field'].browse(field_ids)
        for field in fields:
            if field.field_name in self.env[entity_model]._fields:
                xmlfield = etree.Element(
                    'field',
                    name=field.field_name,
                    string=field.name)
                field_name2 = 'x_valueunit_' + field.field_name[8:]
                xmlfield2 = etree.Element(
                    'field',
                    name=field_name2,
                    string='Unit',
                    nolabel='1',
                    colspan='2')
                group.append(xmlfield)
                group.append(xmlfield2)
                description = self.env[entity_model]._fields[
                    field.field_name].get_description(self.env)
                fvg['fields'][field.field_name] = description
                description2 = self.env[entity_model]._fields[
                    field_name2].get_description(self.env)
                fvg['fields'][field_name2] = description2
                osv.orm.transfer_modifiers_to_node(
                    {'invisible': [
                      ('type_valuation', '!=', field.valuation.id)],
                     'required': field.mandatory},
                    xmlfield)
                osv.orm.transfer_modifiers_to_node(
                    {'invisible': [
                      ('type_valuation', '!=', field.valuation.id)],
                     'required': field.mandatory,
                     'readonly': field.type == 'calc'},
                    xmlfield2)
            else:
                pass
        fvg['arch'] = etree.tostring(doc)
        return fvg


class Observable(models.Model):
    _name = 'rea.value.observable'
    _description = "Observable for value calculation"

    name = fields.Char("Name")
    sequence = fields.Integer("Sequence")
    type = fields.Selection([
        ('konst', 'Constant'),
        ('days', 'Days after'),
        ('time', 'Current Time'),
        ('field', 'Entity field')])
    konst = fields.Float("Value")
    date = fields.Date("Date")
    field = fields.Many2one(
        'ir.model.fields',
        string="Dependent field",
        help="Used as a variable name in the expression")
    value_field = fields.Many2one(
        'rea.valuation.field',
        "Value field")

    def value(self, entity):
        """ get the value of the observable
        """
        if self.type == 'konst':
            return self.konst
        if self.type == 'field' and self.field:
            return getattr(entity, self.field.name)
        raise NotImplementedError
