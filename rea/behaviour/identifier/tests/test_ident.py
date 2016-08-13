from anybox.testing.openerp import SharedSetupTransactionCase


class TestIdent(SharedSetupTransactionCase):

    _module_ns = 'rea'
    _data_files = ('../../../tests/data.xml',)

    @classmethod
    def initTestData(cls):
        super(TestIdent, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.event_types = cls.env['rea.event.type']
        cls.events = cls.env['rea.event']
        cls.ident_setups = cls.env['rea.ident.setup']

    def test_ident(self):
        """
        """
        # we create an automatic numbering for sales
        ident_setup = self.ident_setups.create({
            'name': 'sales numbering',
            'plugin': 'templated_sequence',
            'last_nb': 0,
            'prefix': 'SAJ',
            'suffix': '-',
            'padding': 5,
            'step': 2,
        })
        # we configure the event type 'sale'
        self.event_types.browse(self.ref('rea.event_type_sale')).write({
            'ident_setup': ident_setup.id,
        })
        # now we create two events with no data, they should have a name
        event = {'type': self.ref('rea.event_type_sale')}
        self.assertEquals(self.events.create(event.copy()).name, 'SAJ00002-')
        self.assertEquals(self.events.create(event.copy()).name, 'SAJ00004-')
        ident_setup.write({'step': 3})
        self.assertEquals(self.events.create(event.copy()).name, 'SAJ00007-')
        ident_setup.write({'prefix': 'SAJ%Y%A%U'})
        self.assertEquals(self.events.create(event.copy()).name[:5], 'SAJ20')
