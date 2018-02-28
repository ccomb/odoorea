from odoo import fields, models, api, osv
from lxml import etree


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
                    'ttype': 'char'}).id
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
    def _get_value(self):
        for obj in self:
            obj.type_valuation = obj.type.valuation.id

    type_valuation = fields.Many2one(
        'rea.valuation',
        compute=_get_value)

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
                    string=field.name,
                    required='1' if field.mandatory else '0')
                field_name2 = 'x_valueunit_' + field.field_name[8:]
                xmlfield2 = etree.Element(
                    'field',
                    name=field_name2,
                    string='Unit',
                    nolabel='1',
                    colspan='2',
                    required='1' if field.mandatory else '0')
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
                      ('type_valuation', '!=', field.valuation.id)]},
                    xmlfield)
                osv.orm.transfer_modifiers_to_node(
                    {'invisible': [
                      ('type_valuation', '!=', field.valuation.id)]},
                    xmlfield2)
            else:
                pass
        fvg['arch'] = etree.tostring(doc)
        return fvg
