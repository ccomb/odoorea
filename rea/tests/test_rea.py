from anybox.testing.openerp import SharedSetupTransactionCase


class TestREA(SharedSetupTransactionCase):

    _module_ns = 'rea'
    _data_files = ('data.xml',)

    @classmethod
    def initTestData(cls):
        super(TestREA, cls).initTestData()
        cls.ref = classmethod(lambda cls, xid: cls.env.ref(xid).id)
        cls.agent_type = cls.env['rea.agent.type']

    def test_event_duality(self):
        """
        """
        company = self.agent_type.browse(self.ref('rea.agent_type_company'))
        self.assertEqual(company.name, 'Company')
