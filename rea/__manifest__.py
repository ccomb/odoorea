#    rea module for Odoo
#    Copyright (C) 2016 Anybox (<https://anybox.fr>)
#    rea is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#    rea is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
{
    'name': 'rea',
    'version': '0.1',
    'description': """
    Proof of concept of REA modeling
    """,
    'summary': "REA base models",
    'author': 'Christophe Combelles',
    'website': 'https://anybox.fr',
    'license': 'AGPL-3',
    'category': 'Uncategorized',
    'depends': ['base'],
    'data': [
        'view.xml',
        'structure/resource/security.xml',
        'structure/resource/view.xml',
        'structure/resource/behaviours.xml',
        'structure/resource/conversion/view.xml',
        'structure/event/security.xml',
        'structure/event/view.xml',
        'structure/event/behaviours.xml',
        'structure/agent/security.xml',
        'structure/agent/view.xml',
        'structure/agent/behaviours.xml',
        'structure/commitment/security.xml',
        'structure/commitment/view.xml',
        'structure/commitment/behaviours.xml',
        'structure/contract/security.xml',
        'structure/contract/view.xml',
        'structure/contract/behaviours.xml',
        'structure/event/duality/security.xml',
        'structure/event/duality/view.xml',
        'structure/event/duality/behaviours.xml',
        'structure/fulfillment/security.xml',
        'structure/fulfillment/view.xml',
        'structure/fulfillment/behaviours.xml',
        'structure/matclaim/security.xml',
        'structure/matclaim/view.xml',
        'structure/matclaim/behaviours.xml',
        'behaviour/identifier/view.xml',
        'behaviour/lifecycle/view.xml',
        'behaviour/observable/view.xml',
        'behaviour/property/view.xml',
        'base/res_users.xml',
    ],
    'demo': [
    ],
    'auto_install': False,
    'web': False,
    'post_load': None,
    'application': True,
    'installable': True,
    'sequence': 150,
    'external_dependencies': [],
}
