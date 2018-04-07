from odoo import fields, models, api, osv
from odoo.exceptions import MissingError
from lxml import etree
import time
import pint
ureg = pint.UnitRegistry()


class UnitOfMeasure(models.Model):
    """ Unit of measure of values
    """
    _name = 'rea.uom'
    _description = "Unit of measure"

    name = fields.Char(
        'Short name')
    description = fields.Char(
        'Long name')

    @api.model
    def create(self, vals):
        try:
            ureg.parse_units(vals['name'])
        except:
            raise MissingError("This unit does not exist")
        return super(UnitOfMeasure, self).create(vals)


class PropertyField(models.Model):
    """Setup for a property field
    """
    _name = 'rea.property.field'
    _description = "Setup for a Property field"

    name = fields.Char(string="name", required=True, index=True)
    mandatory = fields.Boolean("Mandatory")
    field_name = fields.Char(
        string="Field name")
    propertyconfig = fields.Many2one(
        'rea.property.config',
        help=u"The configuration this fiels belongs to",
        ondelete='cascade')
    field = fields.Many2one(
        'ir.model.fields',
        "Created field",
        required=True,
        ondelete='restrict')
    type = fields.Selection([
        ('konst', 'Constant'),
        ('calc', 'Calculation')])
    observables = fields.Many2many(
        'rea.observable',
        string="Observables")
    expression = fields.Char(
        "Expression",
        help=("Python expression"))
    resolution = fields.Float(
        "Period",
        help=u"Recompute the property at every period of time")
    next_compute = fields.Datetime(
        "Next computation date")  # TODO also add a last_compute

    def compute_all(self):
        # TODO optimize
        for obj in ('rea_resource', 'rea_event', 'rea_agent',
                    'rea_commitment', 'rea_contract'):
            # compute entity types first...
            self.env.cr.execute(
                "select t1.id, f.id "
                "from %(obj)s_type t1, %(obj)s_type t2, "
                "     rea_property_config c, rea_property_field f "
                "where "
                "    t1.type = t2.id "
                "and f.type = 'calc' "
                "and t2.propertyconfig = c.id "
                "and f.propertyconfig = c.id "
                "and (f.next_compute < '%(now)s' "
                "     or f.next_compute is NULL)"
                % {'obj': obj, 'now': time.strftime('%Y-%m-%d %H:%M:%S')})
            for ent_type_id, field_id in self.env.cr.fetchall():
                field = self.env['rea.property.field'].browse(field_id)
                ent_type = self.env['%s.type' % obj.replace('_', '.')
                                    ].browse(ent_type_id)
                value = field.compute(ent_type).to_compact()
                unit_id = self.env['rea.uom'].search(
                    [('name', '=', u'{:~P}'.format(value.units))]).id
                if not unit_id:
                    raise MissingError(u'Missing unit : {:~P}'
                                       .format(value.units))
                ent_type.write({
                    field.field.name: value.magnitude,
                    'x_unit_%s' % field.field.name[2:]: unit_id})
            # ...then entities
            self.env.cr.execute(
                "select r.id, f.id "
                "from %(obj)s r, %(obj)s_type t, "
                "     rea_property_config c, rea_property_field f "
                "where "
                "    r.type = t.id "
                "and f.type = 'calc' "
                "and t.propertyconfig = c.id "
                "and f.propertyconfig = c.id "
                "and (f.next_compute < '%(now)s' "
                "     or f.next_compute is NULL)"
                % {'obj': obj, 'now': time.strftime('%Y-%m-%d %H:%M:%S')})
            for entity_id, field_id in self.env.cr.fetchall():
                field = self.env['rea.property.field'].browse(field_id)
                entity = self.env[obj.replace('_', '.')].browse(entity_id)
                value = field.compute(entity).to_compact()
                unit_id = self.env['rea.uom'].search(
                    [('name', '=', u'{:~P}'
                                   .format(value.units))]).id
                if not unit_id:
                    raise MissingError(u'Missing unit : {:~P}'
                                       .format(value.units))
                entity.write({
                    field.field.name: value.magnitude,
                    'x_unit_%s' % field.field.name[2:]: unit_id})

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
        """ Create the real field when creating a property field
        Also create the unit field (resource_type)
        """
        field_name = vals.get('field_name')
        model = self.env.context.get('model')
        type_id = self.env.context.get('type_id')
        if not field_name or not model:
            raise Exception("Please create the field from the entity type")
        if field_name != 'name':
            field_name = 'x_prop_%s' % field_name
        vals['field_name'] = field_name
        fields = self.env['ir.model.fields']
        models = self.env['ir.model']
        entity_model = self.env[model]
        entity = entity_model.browse(type_id)
        model = model if entity.subtypes else model[:-5]
        model_id = models.search([('model', '=', model)])[0].id
        existing = fields.search([('model_id', '=', model_id),
                                  ('name', '=', field_name)])
        rt_field_name = 'x_unit_%s' % field_name[2:]
        if existing:
            vals['field'] = existing[0].id
        else:
            if field_name != 'name':
                # magnitude
                vals['field'] = fields.create({
                    'model': model,
                    'model_id': model_id,
                    'name': field_name,
                    'field_description': vals.get('name'),
                    'ttype': 'float'}).id
                # unit
                fields.create({
                    'model': model,
                    'model_id': model_id,
                    'name': rt_field_name,
                    'field_description': '%s Unit' % vals.get('name'),
                    'ttype': 'many2one',
                    'relation': 'rea.uom'}).id
        vals['model'] = model_id
        return super(PropertyField, self).create(vals)

    @api.multi
    def unlink(self):
        for vf in self:
            field = vf.field
            super(PropertyField, self).unlink()
            # TODO prevent deleting existing data
            # delete the concrete field if there are no remaining identfields
            if not self.search([('field_name', '=', field.name),
                                ('field.model', '=', field.model_id.id)]):
                field.search([('model', '=', field.model),
                              ('name', '=', 'x_unit_' + field.name[2:])]
                             ).unlink()
                field.unlink()


class Config(models.Model):
    _name = 'rea.property.config'

    name = fields.Char(string="name", required=True, index=True)
    fields = fields.One2many(
        'rea.property.field',
        'propertyconfig',
        string="Property fields")


class PropertyableType(models.AbstractModel):
    """ field to choose the property fields on the entity type
    """
    _name = 'rea.propertyable.type'

    propertyconfig = fields.Many2one(
        'rea.property.config',
        "Config")


class PropertyableEntity(models.AbstractModel):
    """ entity with configurable properties
    """
    _name = 'rea.propertyable.entity'
    _description = 'Entity with properties'

    @api.depends('type')
    def _get_propertyconfig(self):
        for obj in self:
            obj.type_propertyconfig = obj.type.propertyconfig.id

    type_propertyconfig = fields.Many2one(
        'rea.property.config',
        compute=_get_propertyconfig)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ Add property fields
        """
        fvg = super(PropertyableEntity, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        params = self.env.context.get('params')
        if not params or view_type != 'form':
            return fvg
        doc = etree.fromstring(fvg['arch'])
        group = doc.xpath("//page[@string='Properties']/group/group")[0]
        entity_model = params.get('model', self._name)
        type_model = entity_model + (
            '' if entity_model.endswith('.type') else '.type')
        type_table = self.env[type_model]._table
        self.env.cr.execute('''
            select distinct field.id
            from rea_property_field field, %s type
            where field.propertyconfig = type.propertyconfig''' % type_table)
        field_ids = [t[0] for t in self.env.cr.fetchall()]
        fields = self.env['rea.property.field'].browse(field_ids)
        for field in fields:
            if field.field_name in self.env[entity_model]._fields:
                xmlfield = etree.Element(
                    'field',
                    name=field.field_name,
                    style='max-width: 4em',
                    string=field.name)
                field_name2 = 'x_unit_' + field.field_name[2:]
                xmlfield2 = etree.Element(
                    'field',
                    name=field_name2,
                    string='Unit',
                    nolabel='1',
                    colspan='2',
                    style='margin-left: -5em')
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
                      ('type_propertyconfig', '!=', field.propertyconfig.id)],
                     'required': field.mandatory},
                    xmlfield)
                osv.orm.transfer_modifiers_to_node(
                    {'invisible': [
                      ('type_propertyconfig', '!=', field.propertyconfig.id)],
                     'required': field.mandatory,
                     'readonly': field.type == 'calc'},
                    xmlfield2)
            else:
                pass
        fvg['arch'] = etree.tostring(doc)
        return fvg
