# coding: utf-8
import logging
from lxml import etree
from odoo import models, fields, api, _
from odoo.exceptions import MissingError, UserError
logger = logging.getLogger(__file__)


class Step(models.Model):
    """Lifecycle step of an entity
    Correspond to kanban columns
    """
    _name = 'rea.lifecycle.step'
    _order = 'sequence'

    def _get_entity_types(self):
        if 'base_model_name' not in self.env.context:
            return self.search([]).ids
        return self.search([
            ('type', 'like', '%s,%%' % self.env.context['base_model_name'])]).ids

    type = fields.Reference(
        selection=_get_entity_types,
        string='Entity type',
        required=True)
    name = fields.Char(
        'name',
        size=64,
        required=True,
        translate=True)
    description = fields.Text(
        'Description',
        translate=True)
    state = fields.Char(
        'state',
        size=64,
        required=True)
    sequence = fields.Integer(
        'Sequence',
        help='Sequence')
    #forbidden_rules = fields.Many2many(  # TODO
    #    'rea.policy...',)
    # examples:
    # - missing value on other field
    # - specific value_id on other m2o field
    # - group of the user, etc...


class Lifecycleable(models.AbstractModel):
    """ Add lifecycle features to entities
    """
    _name = 'rea.entity.lifecycleable'

    @api.multi
    def step_previous(self):
        """move the entity to the previous step
        """
        for entity in self:
            if not entity.type:
                raise MissingError(
                    _("Warning: No type defined in the project."))
            etype = ','.join((entity.type._name, str(entity.type.id)))
            steps = entity.step.search([('type', '=', etype)])
            if not steps:
                raise MissingError(
                    _('Warning: No steps defined for this entity'))
            if entity.step == steps[0]:  # first step
                raise UserError(_("Warning: You're already in the first step"))
            elif entity.step not in steps:  # no step
                continue
            else:
                next_step = steps[list(steps).index(entity.step) - 1]
            entity.write({'step': next_step.id})

    @api.multi
    def step_next(self):
        """move the entity to the next step
        """
        for entity in self:
            if not entity.type:
                raise MissingError(
                    _("Warning: No type defined in the project."))
            etype = ','.join((entity.type._name, str(entity.type.id)))
            steps = entity.step.search([('type', '=', etype)])
            if not steps:
                raise MissingError(
                    _('Warning: No steps defined for this entity'))
            if entity.step == steps[-1]:  # last step
                raise UserError(_("Warning: You're already in the last step"))
            elif entity.step not in steps:  # no step
                next_step = steps[0]
            else:
                next_step = steps[list(steps).index(entity.step) + 1]
            entity.write({'step': next_step.id})

    #@api.model
    #def fields_view_get(self, view_id=None, view_type='form',
    #                    toolbar=False, submenu=False):
    #    """ Add lifecycle action buttons
    #    """
    #    fvg = super(Lifecycleable, self).fields_view_get(
    #        view_id=view_id, view_type=view_type,
    #        toolbar=toolbar, submenu=submenu)
    #    if view_type == 'form' and fvg['type'] == 'form':
    #        doc = etree.fromstring(fvg['arch'])
    #        try:
    #            node = doc.xpath("/header")[0]
    #        except:
    #            logger.error("Could not find the header in the view")
    #            return fvg
    #        buttons = []
    #        targets = 
    #        for target in targets:
    #            button = etree.Element("root", name=target.)
    #            button.set()
    #            buttons.append(button)
    #        node.
    #        fvg['arch'] = etree.tostring(doc)
    #    return fvg

    @api.model
    def create(self, values):
        """select the default step
        """
        if not values.get('step'):
            type = self.type.browse(values['type'])
            values['step'] = type.get_first_step()
        return super(Lifecycleable, self).create(values)

    def _domain(self):
        return "[('type','=', '%s,'+str(type))]" % self.type._name

    step = fields.Many2one(
        'rea.lifecycle.step',
        'Step',
        select=True,
        domain=_domain)


class LifecyclableType(models.AbstractModel):
    _name = 'rea.type.lifecycleable'

    def get_first_step(self):
        """ Return the id of the first step of a type"""
        if len(self) == 0:
            return False
        steps = [(s.sequence, s.id) for s in self.step_ids]
        return sorted(steps)[0][1] if len(steps) else False

    def _get_steps(self):
        for etype in self:
            etype.step_ids = self.env['rea.lifecycle.step'].search([('type', '=', ','.join((etype._name, str(etype.id))))])

    def _set_steps(self):
        for etype in self:
            strtype = ','.join((etype._name, str(etype.id)))
            existing = etype.step_ids.search([('type', '=', strtype)]).ids
            modified = etype.step_ids.ids
            for step in etype.step_ids:
                if step.id:
                    values = step.read(load=True)[0]
                    values['type'] = strtype
                    step.write(values)
                else:
                    values = dict(step._cache)
                    values['type'] = strtype
                    step.create(values)
            etype.step_ids.browse(set(existing)-set(modified)).unlink()

    step_ids = fields.One2many(
        'rea.lifecycle.step',
        compute=_get_steps,
        inverse=_set_steps,
        string='Steps',
        copy=True,
        help="The steps associated to this type")
