from anybox.testing.openerp import SharedSetupTransactionCase


class TestREA(SharedSetupTransactionCase):

    _module_ns = 'rea'
    _data_files = ('data.xml',)

    @classmethod
    def initTestData(cls):
        super(TestREA, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.agents = cls.env['rea.agent']
        cls.events = cls.env['rea.event']
        cls.processes = cls.env['rea.process']

    def test_event_duality(self):
        """
        """
        anybox = self.agents.browse(self.ref('rea.agent_anybox'))
        self.assertEqual(anybox.name, 'Anybox')
        # we want to sell 2 usb keys for 20 euro.
        # First we select the relevant process type
        sale_process = self.processes.create({
            'name': 'SAP00001',
            'type': self.ref('rea.process_type_sale'),
        })
        # create sale events for two usb keys, serial 001 and 002
        # These events represent transfer of ownership. Not delivery.
        sale1 = self.events.create({
            'name': "SAJ00001",
            'type': self.ref('rea.event_type_sale'),
            'process': sale_process.id,
            'provider': self.ref('rea.agent_anybox'),
            'receiver': self.ref('rea.agent_acme'),
            'date': '2016/07/29',
            'resource': self.ref('rea.res_usbkey1'),
        })
        sale2 = self.events.create({
            'name': "SAJ00002",
            'type': self.ref('rea.event_type_sale'),
            'process': sale_process.id,
            'provider': self.ref('rea.agent_anybox'),
            'receiver': self.ref('rea.agent_acme'),
            'date': '2016/07/29',
            'resource': self.ref('rea.res_usbkey2'),
        })
        # create a payment event for the usb key
        payment = self.events.create({
            'name': "BNK00001",
            'type': self.ref('rea.event_type_payment'),
            'receiver': self.ref('rea.agent_anybox'),
            'provider': self.ref('rea.agent_acme'),
            'date': '2016/07/29',
            'resource': self.ref('rea.res_20_euro'),
        })
