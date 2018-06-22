# coding: utf-8
import logging
from lxml import etree
from odoo import models, fields, api, _, osv
from odoo.exceptions import MissingError, UserError, ValidationError
logger = logging.getLogger(__file__)


class Lifecycle(models.Model):
    """Lifecycle containing steps and transitions
    """
    _name = 'rea.lifecycle'

    name = fields.Char(
        'Name',
        required=True,
        translate=True,
        help="Name of the lifecycle")
    description = fields.Text(
        'Description',
        translate=True)
    steps = fields.One2many(
        'rea.lifecycle.step',
        'lifecycle',
        string='Steps',
        copy=True,
        help="List of possible steps for contracts of this type. "
             "Steps correspond to the columns of the kanban view")
    transitions = fields.One2many(
        'rea.lifecycle.transition',
        'lifecycle',
        string='Transitions',
        copy=True,
        help="List of transition buttons between steps for contracts "
             "of this type. Buttons appear in the form view of the contracts")


class Step(models.Model):
    """Lifecycle step of an entity
    Correspond to kanban columns
    """
    _name = 'rea.lifecycle.step'
    _order = 'sequence, id'

    lifecycle = fields.Many2one(
        'rea.lifecycle',
        string='Lifecycle',
        required=True,
        ondelete='cascade')
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
        string='Outgoing Transitions')
    incomings = fields.One2many(
        'rea.lifecycle.transition',
        'target',
        readonly=True,
        string='Incoming Transitions')
    #forbidden_rules = fields.Many2many(  # TODO
    #    'rea.policy...',)
    # examples:
    # - missing value on other field
    # - specific value_id on other m2o field
    # - group of the user, etc...
    forbid_deletion = fields.Boolean(
        u"Forbid deletion",
        default=False,
        help=u"Forbid to delete the entity at this step")


class Transition(models.Model):
    """Transition between two steps
    Allow to add dynamic transition buttons
    """
    _name = 'rea.lifecycle.transition'

    lifecycle = fields.Many2one(
        'rea.lifecycle',
        string='Lifecycle',
        required=True,
        ondelete='cascade')
    name = fields.Char(
        'Name',
        required=True,
        translate=True,
        help="Used for the transition button")
    code = fields.Char(
        'Code',
        required=True,
        translate=True,
        help="Used to compare on different types")
    description = fields.Text(
        'Description',
        help="Add more information on the transition")
    origin = fields.Many2one(
        'rea.lifecycle.step',
        'Origin',
        domain="[('lifecycle','=',lifecycle)]")
    target = fields.Many2one(
        'rea.lifecycle.step',
        'Target',
        domain="[('lifecycle','=',lifecycle)]")
    button = fields.Boolean(
        "Add a button",
        help="Add a transition button on entities of this type")
    primary = fields.Boolean(
        'Primary button',
        help="Primary buttons are highlighted and correspond "
             "to the logical next action")


class Lifecycleable(models.AbstractModel):
    """ Add lifecycle behaviour to entities
    """
    _name = 'rea.lifecycleable.entity'

    def steps(self):
        if not self.type:
            raise MissingError(
                _("Warning: No type defined"))
        if not self.type.lifecycle:
            raise MissingError(
                _("Warning: No lifecycle defined in the type"))
        steps = self.type.lifecycle.steps
        if not steps:
            raise MissingError(
                _("Warning: No steps defined in the lifecycle of the type"))
        return steps

    @api.multi
    def go_previous(self):
        """ask transition going to the previous step
        """
        for entity in self:
            if not entity.step:
                entity.write({'step': entity.type.get_first_step()})
                continue
            if entity.transition.target == entity.step:
                self.cancel_transition()
                continue
            transitions = entity.step.transitions
            # guess what is previous by sorting on id and sequence
            sorted_trans = sorted(
                [(t.target.sequence, t.target.id, t) for t in transitions]
                + [(entity.step.sequence, entity.step.id, None)],
                key=lambda x: x[0:2])
            if sorted_trans[0][2] is None:
                if not self.env.context.get('transition_no_fail'):
                    raise UserError(
                        _("Warning: {} \"{}\" seems already in the first step"
                          .format(entity._description, entity.name)))
            transition = sorted_trans[
                sorted_trans.index((entity.step.sequence, entity.step.id, None)
                                   ) - 1][2]
            entity.write({'transition': transition.id})

    @api.multi
    def go_next(self):
        """ask transition going to the next step
        """
        for entity in self:
            if not entity.step:
                entity.write({'step': entity.type.get_first_step()})
                continue
            if entity.transition.target == entity.step:
                self.cancel_transition()
                continue
            transitions = entity.step.transitions
            # guess what is next by sorting on id and sequence
            sorted_trans = sorted(
                [(t.target.sequence, t.target.id, t) for t in transitions]
                + [(entity.step.sequence, entity.step.id, None)],
                key=lambda x: x[0:2])
            if sorted_trans[-1][2] is None:
                if not self.env.context.get('transition_no_fail'):
                    raise UserError(
                        _("Warning: {} \"{}\" seems already in the last step"
                          .format(entity._description, entity.name)))
            transition = sorted_trans[
                sorted_trans.index((entity.step.sequence, entity.step.id, None)
                                   ) + 1][2]
            entity.write({'transition': transition.id})

    def start_transition(self, transition=None, no_fail=False):
        """ Mark the transition as started but do nothin yet
        """
        for entity in self:
            trans_id = transition.id or int(self.env.context['transition'])
            if entity.transition and not no_fail:
                raise UserError(
                    _("Transition is already started. "
                      "You can still cancel it before it is handled"))
            if trans_id:
                entity.write({'transition': trans_id})

    def cancel_transition(self):
        for entity in self:
            entity.write({
                'transition': False,
                'step': entity.transition.origin.id or entity.step.id})
            for field in entity.type.subobjects:
                getattr(entity, field.name).cancel_transition()

    @api.one
    def do_transition(self):
        target = self.type.lifecycle.transitions.browse(transition_id).target
        pass

    def write(self, vals):
        """ only step: add transition
        only transition : transition
        step and transition : only valid if transition is False
        """
        # TODO: allow to run two transitions at the same time?
        step_id, trans_id = vals.get('step'), vals.get('transition')
        wanted_step = self.env['rea.lifecycle.step'].browse(step_id)
        for entity in self:
            # allow to specify a state instead of a step id
            if 'state' in vals:
                steps = entity.step.search([
                    ('state', '=', vals['state']),
                    ('lifecycle', '=', entity.type.lifecycle.id)])
                if len(steps) == 1:
                    vals['step'] = step_id = steps[0].id
                    wanted_step = entity.step.browse(step_id)
                else:
                    raise UserError(_("Wrong configuration: these steps have"
                                      " the same state: %s"
                                      % ', '.join([s.name for s in steps])))

            # if a transition is started, only accept a step cancelling it
            if entity.transition:
                if step_id:
                    if wanted_step.state != entity.transition.origin.state:
                        if not self.env.context.get('transition_no_fail'):
                            raise UserError(
                                _("A transition is already started, you can "
                                  "only set the step back to the origin "
                                  "of the transition"))

                if trans_id:
                    new_trans = entity.transition.browse(trans_id)
                    if (new_trans.target != entity.transition.origin
                            and new_trans.origin != entity.transition.target):
                        if not self.env.context.get('transition_no_fail'):
                            raise UserError(
                                _("A transition is already started, you can "
                                  "only set the reverse transition of the "
                                  "current transition"))

                vals['transition'] = False
            else:
                # check the wanted step is valid
                if wanted_step:
                    if wanted_step == entity.step:
                        continue
                    # find the possible transition
                    targets = [t.target.id for t in entity.step.transitions]
                    if wanted_step.id not in targets:
                        if not self.env.context.get('transition_no_fail'):
                            raise UserError(
                                _("Warning: {} \"{}\" "
                                  "has no transitions to this step"
                                  .format(entity._description, entity.name)))
                    transitions = [t for t in entity.step.transitions
                                   if t.target.state == wanted_step.state]
                    if len(transitions) == 1:
                        vals['transition'] = trans_id = transitions[0].id
                    else:
                        if not self.env.context.get('transition_no_fail'):
                            raise UserError(
                                _("Not exactly one transition exists for this "
                                  "target step"))
                elif trans_id:
                    wanted_trans = entity.transition.browse(trans_id)
                    if wanted_trans.origin.state != entity.step.state:
                        raise UserError(
                            _("Invalid transition for the current step"))
                    vals['step'] = step_id = wanted_trans.target.id
                    wanted_step = entity.step.browse(step_id)

        result = super(Lifecycleable, self).write(vals)

        # apply the same state for subobjects
        if step_id:
            if 'transition' in vals:
                del vals['transition']
            for entity in self:
                for field in entity.type.subobjects:
                    getattr(entity, field.name).with_context(
                        {'transition_no_fail': True}
                        ).write({'state': wanted_step.state})
        return result

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        """ Add lifecycle action buttons
        """
        fvg = super(Lifecycleable, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        params = self.env.context.get('params')
        if not params or view_type != 'form':
            return fvg
        doc = etree.fromstring(fvg['arch'])
        header = doc.xpath("/form/header")[0]
        model = params.get('model', self._name)
        model = model + ('.type' if not model.endswith('.type') else '')
        table = self.env[model]._table
        self.env.cr.execute('''
            select distinct transition.id
            from rea_lifecycle_transition transition, %s type
            where transition.lifecycle = type.lifecycle''' % table)
        trans_ids = [t[0] for t in self.env.cr.fetchall()]
        transitions = self.env['rea.lifecycle.transition'].browse(trans_ids)
        for transition in transitions:
            button = etree.Element(
                "button",
                name='start_transition',
                context="{'transition': '%s'}" % transition.id,
                string=transition.name,
                type='object')
            button.set('class',
                       "btn btn-primary" if transition.primary else "btn")
            state = transition.origin.state
            osv.orm.transfer_modifiers_to_node(
                {'invisible': [
                    '|',
                    ('type_lifecycle', '!=', transition.lifecycle.id),
                    ('state', '!=', state)]}, button)
            header.append(button)
        fvg['arch'] = etree.tostring(doc)
        return fvg

    @api.model
    def create(self, values):
        """select the default step
        """
        if values.get('type') and not values.get('step'):
            type = self.type.browse(values['type'])
            values['step'] = type.get_first_step()
        return super(Lifecycleable, self).create(values)

    @api.multi
    @api.depends('step')
    def _get_state(self):
        for e in self:
            e.state = e.step.state

    @api.multi
    @api.depends('type')
    def _get_lifecycle(self):
        for entity in self:
            entity.type_lifecycle = entity.type.lifecycle

    def unlink(self):
        for e in self:
            if e.step.forbid_deletion:
                raise ValidationError(
                    u"Entity ({}) cannot be deleted "
                    u"because its current step ({}) forbids it"
                    .format(e.name, e.step.name))
            else:
                super(Lifecycleable, e).unlink()

    type_lifecycle = fields.Many2one(
        'rea.lifecycle',
        'Lifecycle',
        compute=_get_lifecycle)
    step = fields.Many2one(
        'rea.lifecycle.step',
        'Current Step',
        index=True,
        copy=False,
        domain="[('lifecycle','=',type_lifecycle)]")
    transition = fields.Many2one(
        'rea.lifecycle.transition',
        'Transition started',
        help="Contains the transition in demand but not run yet",
        index=True,
        copy=False,
        domain="[('lifecycle','=',type_lifecycle)]")
    state = fields.Char(
        'state',
        store=True,
        compute=_get_state)


class LifecyclableType(models.AbstractModel):
    """Abstract class adding lifecycle behaviour on entity types
    """
    _name = 'rea.lifecycleable.type'

    def get_first_step(self):
        """ Return the id of the first step of a type"""
        if len(self) == 0:
            return False
        step_ids = [(s.sequence, s.id) for s in self.lifecycle.steps]
        return sorted(step_ids)[0][1] if len(step_ids) else False

    @api.one
    @api.constrains('subobjects')
    def check_subobject_states(self):
        for o in self:
            for f in o.subobjects:
                if 'step' not in self.env[o.subobjects.relation]._fields:
                    raise ValidationError(
                        u"This subobjects corresponding to this field "
                        u"has no lifecycles: {}"
                        .format(f.display_name))

    lifecycle = fields.Many2one(
        'rea.lifecycle',
        "Lifecycle")
    subobjects = fields.Many2many(
        'ir.model.fields',
        domain="['|', ('ttype','=','one2many'), ('ttype','=','many2many')]",
        help=u"When changing the step of the current object, the sub-objects "
             u"in the specified fields will be changed as well, "
             u"using the same state")
