from odoo import fields, models, api, osv
from lxml import etree
import time


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
        ondelete='cascade')
    model = fields.Many2one(
        'ir.model',
        string="Related model")
    field = fields.Many2one(
        'ir.model.fields',
        "Created field",
        required=True,
        ondelete='restrict')
    type = fields.Selection([
        ('konst', 'Constant'),
        ('calc', 'Calculation')])
    calculation = fields.Many2one(
        'rea.value.calculation',
        string=u"Calculation method")

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
                vals['field'] = fields.create({
                    'model': model,
                    'model_id': model_id,
                    'name': field_name,
                    #'depends': 
                    #'compute':
                    #    "for r in self:\n\tr['%s']=self.compute_field('%s')"
                    #    % (field_name, field_name)
                    #    if self.type == 'calc' else False,
                    'ttype': 'float'}).id
                fields.create({
                    'model': model,
                    'model_id': model_id,
                    'name': rt_field_name,
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
        "Valuation Type")


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

    #def compute_field(self):
    #    import pdb; pdb.set_trace()

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

    sequence = fields.Integer("Sequence")
    name = fields.Char("Name")
    type = fields.Selection([
        ('konst', 'Constant'),
        ('days', 'Days after'),
        ('time', 'Current Time'),
        ('field', 'Entity field')])
    konst = fields.Float("Value")
    date = fields.Date("Date")
    field = fields.Many2one(
        'ir.model.fields',
        string="Dependent field")
    calculation = fields.Many2one(
        'rea.value.calculation',
        "Calculation")

    def value(self, entity):
        """ get the value of the observable
        """
        if self.type == 'konst':
            def obs():
                return self.konst
            return obs
        if self.type == 'field' and self.field:
            def obs():
                return getattr(entity, self.field.name)
            return obs
        raise NotImplementedError


class Calculation(models.Model):
    """ Calculate value fields depending on other fields
    """
    _name = 'rea.value.calculation'
    _description = u"Calculate value fields"

    expression = fields.Char(
        "Expression",
        help=("Python expression"))

    observables = fields.One2many(
        'rea.value.observable',
        'calculation',
        string="Observables")

    resolution = fields.Float(
        "Period",
        help=u"Recompute the value at every period of time")

    next_valuation = fields.Date(
        "Next valuation date")

    def compute_all(self):
        self.env.cr.execute("select r.id, f.id, c.id  from rea_resource r, rea_resource_type t, rea_valuation v, rea_valuation_field f, rea_value_calculation c where r.type = t.id and t.valuation = v.id and f.valuation = v.id and (c.next_valuation < '%s' or c.next_valuation is NULL)" % time.strftime('%Y-%m-%d %H:%M:%S'))
        for resource_id, field_id, calculation_id in self.env.cr.fetchall():
            field = self.env['rea.valuation.field'].browse(field_id)
            resource = self.env['rea.resource'].browse(resource_id)
            value = self.browse(calculation_id).compute(resource, field)
            resource.write({field.field.name: value})

    def compute(self, entity, field):
        """given a calculation and an entity, return the new value of the field
        """
        for calc in self:
            import pdb; pdb.set_trace()
            localvars = {o.name: o.value(entity) for o in calc.observables}
            # TODO memoize and use a resolution (day, minute, etc.)
            # to avoid recreating the commitment at each term execution
            # FIXME unsafe
            value = eval(self.expression,
                         {"__builtins__": {}},
                         localvars)
            return value
            # _function(time.strftime('%Y-%m-%d %H:%M:%S'))
