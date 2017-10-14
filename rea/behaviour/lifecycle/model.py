# coding: utf-8
import logging
from lxml import etree
from odoo import models, fields, api, _, osv
from odoo.exceptions import MissingError, UserError
logger = logging.getLogger(__file__)


class Step(models.Model):
    """Lifecycle step of an entity
    Correspond to kanban columns
    """
    _name = 'rea.lifecycle.step'
    _order = 'sequence'

    def _get_entity_types(self):
        model = (self.env.context.get('base_model_name')
                 or self.env.context.get('model'))
        if not model:
            return self.search([]).ids
        return self.search([
            ('type', 'like', '%s,%%' % model)]).ids

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
    transitions = fields.One2many(
        'rea.lifecycle.transition',
        'origin',
        readonly=True,
        string='Transitions')
    #forbidden_rules = fields.Many2many(  # TODO
    #    'rea.policy...',)
    # examples:
    # - missing value on other field
    # - specific value_id on other m2o field
    # - group of the user, etc...


class Transition(models.Model):
    """Transition between two steps
    Allow to add dynamic transition buttons
    """
    _name = 'rea.lifecycle.transition'

    def _get_entity_types(self):
        model = (self.env.context.get('base_model_name')
                 or self.env.context.get('model'))
        if not model:
            return self.search([]).ids
        return self.search([
            ('type', 'like', '%s,%%' % model)]).ids

    def _domain(self):
        model = (self.env.context.get('base_model_name')
                 or self.env.context.get('model'))
        return "[('type', 'like', '%s,%%')]" % model

    type = fields.Reference(
        selection=_get_entity_types,
        string='Entity type',
        required=True)
    name = fields.Char(
        'Name',
        required=True,
        translate=True,
        help="Used for the transition button")
    description = fields.Text(
        'Description',
        help="Add more information on the transition")
    origin = fields.Many2one(
        'rea.lifecycle.step',
        'Origin',
        domain=_domain)
    target = fields.Many2one(
        'rea.lifecycle.step',
        'Target',
        domain=_domain)
    button = fields.Boolean(
        "Add a button",
        help="Add a transition button on entities of this type")


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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ Add lifecycle action buttons
        """
        fvg = super(Lifecycleable, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type != 'form' or fvg['type'] != 'form':
            return fvg
        doc = etree.fromstring(fvg['arch'])
        header = doc.xpath("/form/header")[0]
        context = self.env.context
        if 'params' in context and 'model' in context['params']:
            model = self.env.context['params']['model']
        else:
            model = self._name
        transitions = self.env['rea.lifecycle.transition'].search([
            ('type', 'like', '%s.type,%%' % model)])
        for transition in transitions:
            button = etree.Element(
                "button",
                name=transition.name,
                string=transition.name,
                type='object')
            state = transition.origin.state
            osv.orm.transfer_modifiers_to_node(
                {'invisible': [["state", "!=", state]]}, button)
            header.append(button)
        fvg['arch'] = etree.tostring(doc)
        return fvg

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

    def _get_state(self):
        for e in self:
            e.state = e.step.state

    step = fields.Many2one(
        'rea.lifecycle.step',
        'Step',
        index=True,
        domain=_domain)
    state = fields.Char(
        'state',
        compute=_get_state)


class LifecyclableType(models.AbstractModel):
    _name = 'rea.type.lifecycleable'

    def get_first_step(self):
        """ Return the id of the first step of a type"""
        if len(self) == 0:
            return False
        step_ids = [(s.sequence, s.id) for s in self.steps]
        return sorted(step_ids)[0][1] if len(step_ids) else False

    def _get_steps(self):
        for etype in self:
            etype.steps = self.env['rea.lifecycle.step'].search(
                [('type', '=', ','.join((etype._name, str(etype.id))))])

    def _set_steps(self):
        for etype in self:
            strtype = ','.join((etype._name, str(etype.id)))
            existing = etype.steps.search([('type', '=', strtype)])
            modified = etype.steps
            for step in etype.steps:
                if step.id:
                    values = step.read(load=True)[0]
                    values['type'] = strtype
                    del values['transitions']
                    step.write(values)
                else:
                    values = dict(step._cache)
                    values['type'] = strtype
                    step.create(values)
            etype.steps.browse(set(existing)-set(modified)).unlink()

    def _get_transitions(self):
        for etype in self:
            etype.transitions = self.env['rea.lifecycle.transition'].search(
                [('type', '=', ','.join((etype._name, str(etype.id))))])

    def _set_transitions(self):
        for etype in self:
            strtype = ','.join((etype._name, str(etype.id)))
            existing = etype.transitions.search([('type', '=', strtype)])
            modified = etype.transitions
            for transition in etype.transitions:
                if transition.id:
                    values = transition.read(load=True)[0]
                    values['type'] = strtype
                    transition.write(values)
                else:
                    values = dict(transition._cache)
                    values['type'] = strtype
                    transition.create(values)
            etype.transitions.browse(set(existing)-set(modified)).unlink()

    steps = fields.One2many(
        'rea.lifecycle.step',
        compute=_get_steps,
        inverse=_set_steps,
        string='Steps',
        copy=True,
        help="List of possible steps for contracts of this type. "
             "Steps correspond to the columns of the kanban view")
    transitions = fields.One2many(
        'rea.lifecycle.transition',
        compute=_get_transitions,
        inverse=_set_transitions,
        string='Transitions',
        copy=True,
        help="List of transition buttons between steps for contracts "
             "of this type. Buttons appear in the form view of the contracts")
