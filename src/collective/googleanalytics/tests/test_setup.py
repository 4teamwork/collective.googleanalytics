
from Products.CMFCore.utils import getToolByName
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.app.testing import quickInstallProduct
from collective.googleanalytics.report import AnalyticsReport
from collective.googleanalytics.tests.base import FunctionalTestCase
from collective.googleanalytics.vocabularies import getProfiles
from collective.googleanalytics.vocabularies import getWebProperties


class TestInstall(FunctionalTestCase):

    def test_installation_creates_tool(self):
        """
        Test that the portal_analytics tool is created.
        """
        analytics_tool = getToolByName(self.portal, 'portal_analytics', None)
        self.assertNotEqual(analytics_tool, None)

    def test_installation_creates_reports(self):
        """
        Test that the Analytics reports defined in analytics.xml are
        imported correctly.
        """
        analytics_tool = getToolByName(self.portal, 'portal_analytics', None)

        # Test the 'Site Visits: Line Chart' report.
        report = analytics_tool.get('site-visits-line', None)
        self.assertNotEqual(report, None)
        self.assertEqual(report.title, 'Site Visits: Line Chart')
        self.assertTrue('ga:visits' in report.metrics)

        # Test the 'Top 5 Page Views: Table' report.
        report = analytics_tool.get('top-5-pageviews-table', None)
        self.assertNotEqual(report, None)
        self.assertEqual(report.columns, "python:['URL', 'Views']")
        self.assertEqual(report.row_repeat, "python:dimension('ga:pagePath')")
        self.assertEqual(report.rows, "python:[row, metric('ga:pageviews', {'ga:pagePath': row})]")

        # Test the 'Top 5 Sources: Table' report.
        report = analytics_tool.get('top-5-sources-table', None)
        self.assertNotEqual(report, None)
        self.assertEqual(report.viz_type, 'Table')
        self.assertNotEqual(report.body, '')


class TestReinstall(FunctionalTestCase):

    def test_reinstallation_preserves_settings(self):
        """
        Test that reinstalling the product does not wipe out the settings
        stored on the portal_analytics tool.
        """
        # Set some properties on the portal_analytics tool.
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        analytics_tool.auth_token = u'abc123'
        analytics_tool.cache_interval = 100

        # Reinstall the product.
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        quickInstallProduct(self.portal, 'collective.googleanalytics', reinstall=False)
        # quick_installer = getToolByName(self.portal, "portal_quickinstaller")
        # import pdb; pdb.set_trace()
        # quick_installer.reinstallProducts(
        #     products=['collective.googleanalytics', ]
        # )

        # Make sure the properties are still set.
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        self.assertEqual(analytics_tool.auth_token, u'abc123')
        self.assertEqual(analytics_tool.cache_interval, 100)

    def test_reinstallation_preserves_reports(self):
        """
        Test that reinstalling the product does not wipe out custom reports.
        """
        # Make some reports.
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        analytics_tool['foo'] = AnalyticsReport('foo')
        analytics_tool['bar'] = AnalyticsReport('bar')

        # Reinstall the product.
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        quickInstallProduct(self.portal, 'collective.googleanalytics', reinstall=False)
        # quick_installer = getToolByName(self.portal, "portal_quickinstaller")
        # quick_installer.reinstallProducts(
        #     products=['collective.googleanalytics', ]
        # )

        # Make sure the reports are still there.
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        report = analytics_tool.get('foo', None)
        self.assertNotEqual(report, None)

        report = analytics_tool.get('bar', None)
        self.assertNotEqual(report, None)


class DummyTool(object):
    auth_token = 'foo'
    accounts = None

    def makeClientRequest(self, api_request):
        return self.accounts

    def makeCachedRequest(self, api_request):
        return self.accounts

    def is_auth(self):
        return True


class TestUnicode(FunctionalTestCase):

    def setUp(self):
        FunctionalTestCase.setUp(self)
        self.oldtool = getToolByName(self.portal, 'portal_analytics')
        self.portal.portal_analytics = DummyTool()

    def tearDown(self):
        self.portal.portal_analytics = self.oldtool
        FunctionalTestCase.tearDown(self)

    def test_cga_unicode_problems(self):
        # fails with unicode error with c.googleanalytics <= 1.4.1
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        analytics_tool.accounts = [{
            u'name': u'A - Nantes D\xe9veloppement',
            u'id': 'foo',
            u'tableId': 'foo'
        }]
        accounts = getProfiles(analytics_tool)
        self.assertEquals(
            accounts.by_value['foo'].title,
            u'A - Nantes D\xe9veloppement'
        )
        props = getWebProperties(analytics_tool)
        self.assertEquals(
            props.by_value['foo'].title,
            u'A - Nantes D\xe9veloppement'
        )

    def test_cga_overlong_profile_names(self):
        # fails with unicode error with c.googleanalytics <= 1.4.1
        analytics_tool = getToolByName(self.portal, 'portal_analytics')
        analytics_tool.accounts = [{
            u'name': u'A - Nantes D\xe9veloppement a very long profile name and continuing',
            u'id': 'foo',
            u'tableId': 'foo'
        }]
        accounts = getProfiles(analytics_tool)
        self.assertEquals(
            accounts.by_value['foo'].title,
            u'A - Nantes D\xe9veloppement a very long ...'
        )
        props = getWebProperties(analytics_tool)
        self.assertEquals(
            props.by_value['foo'].title,
            u'A - Nantes D\xe9veloppement a very long ...'
        )
