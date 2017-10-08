# coding: utf-8
import logging
from lxml import etree
from odoo import orm, models, fields, api, _
from odoo.exceptions import MissingError, UserError
logger = logging.getLogger(__file__)



class Step(models.AbstractModel):
    """Lifecycle step of an entity
    Correspond to kanban columns
    """
    _name = 'rea.lifecycle.step'
    _order = 'sequence'

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
    progress = fields.Float(
        'Progress',
        help='Progress value of the entity reaching this step')
    #forbidden_rules = fields.Many2many(  # TODO
    #    'rea.policy...',)
    # examples:
    # - missing value on other field
    # - specific value_id on other m2o field
    # - group of the user, etc...


class Entity(models.AbstractModel):
    """ Add lifecycle features to entities
    """
    _name = 'rea.behaviour.lifecycle'

    @api.multi
    def step_previous(self):
        """move the entity to the previous step
        """
        STEP = self.env[self._behaviours['step']]
        for entity in self:
            steps = STEP.search([('type', '=', entity.type.id)])
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
        STEP = self.env[self._behaviours['step']]
        for entity in self:
            if not entity.type:
                raise MissingError(
                    _("Warning: No type defined in the project."))
            steps = STEP.search([('type', '=', entity.type.id)])
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
        fvg = super(Entity, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)
        if view_type == 'form' and fvg['type'] == 'form':
            doc = etree.fromstring(fvg['arch'])
            try:
                node = doc.xpath("/header")[0]
            except:
                logger.error("Could not find the header in the view")
                return fvg
            buttons = []
            targets = 
            for target in targets:
                button = etree.Element("root", name=target.)
                button.set()
                buttons.append(button)
            node.
            fvg['arch'] = etree.tostring(doc)
        return fvg


    progress = fields.Float(
        'Progress',
        default=0.0,
        select=True,
        group_operator="avg")
