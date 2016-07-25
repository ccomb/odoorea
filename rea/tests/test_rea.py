from anybox.testing.openerp import SharedSetupTransactionCase


class TestREA(SharedSetupTransactionCase):

    _module_ns = 'rea'
    _data_files = ('data.xml',)

    @classmethod
    def initTestData(cls):
        super(TestREA, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)

    def test_event_duality(self):
        """
        """
        self.assertEqual(self.ref('agent_type_company').name, 'Company')
