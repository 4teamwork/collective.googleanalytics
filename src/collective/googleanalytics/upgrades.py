
from Products.CMFCore.utils import getToolByName
from collective.googleanalytics.interfaces.utility import IAnalyticsSchema
from plone.registry.interfaces import IRegistry
from zope.annotation import IAnnotations
from zope.component import getUtility


def null_upgrade_step(setup_tool):
    """
    This is a null upgrade, use it when nothing happens
    """
    pass


def upgrade_10a2_to_10a3(setup_tool):
    """
    Remove external javascript from the registry and use a viewlet instead.
    Import new reports.
    """

    name = 'profile-collective.googleanalytics:upgrade_10a2_10a3'
    setup_tool.runAllImportStepsFromProfile(name)


def upgrade_10a4_to_10b1(setup_tool):
    """
    Update reports to use new attributes and reimport default reports.
    """

    analytics_tool = getToolByName(setup_tool, 'portal_analytics')
    reports = analytics_tool.getReports()

    BODY_TEMPLATE = """<!--
    %s
    <div tal:replace="structure view/visualization"></div>
    %s
    -->
    This report needs to be updated to use the new table building fields
    introduced in collective.googleanalytics 1.0b1.
    """

    COLUMNS_TEMPLATE = """<!--
    COLUMN LABELS:
    %s

    COLUMN EXPRESSIONS:
    %s
    -->
    """

    def map_filter(old_filter):
        """
        Maps an old filter expression to a new one.
        """

        if old_filter == 'string:ga:pagePath==${page_url}':
            return 'page_filter'
        if old_filter == 'string:ga:nextPagePath==${page_url}':
            return 'nextpage_filter'
        if old_filter == 'string:ga:previousPagePath==${page_url}':
            return 'previouspage_filter'
        return old_filter

    for report in reports:
        if not hasattr(report, 'plugin_names'):
            report.plugin_names = []

            if hasattr(report, 'is_page_specific') and report.is_page_specific:
                report.plugin_names.append(u'Contextual Results')

            if hasattr(report, 'is_page_specific'):
                del report.is_page_specific

            report.plugin_names.append(u'Variable Date Range')

        if hasattr(report, 'filters'):
            report.filters = [map_filter(f) for f in report.filters]

        if not hasattr(report, 'start_date'):
            report.start_date = u''

        if not hasattr(report, 'end_date'):
            report.end_date = u''

        if type(report.max_results) is int:
            report.max_results = u'python:%i' % report.max_results

        if hasattr(report, 'introduction') and hasattr(report, 'conclusion'):
            report.body = BODY_TEMPLATE % (
                report.introduction,
                report.conclusion,
            )

            del report.introduction
            del report.conclusion

        if hasattr(report, 'column_labels') and hasattr(report, 'column_exps'):
            report.columns = report.row_repeat = report.rows = ''

            report.body += COLUMNS_TEMPLATE % (
                report.column_labels,
                report.column_exps,
            )

            del report.column_labels
            del report.column_exps

        if report.i18n_domain == 'analytics':
            report.i18n_domain = 'collective.googleanalytics'

    profile_id = 'profile-collective.googleanalytics:upgrade_10a4_10b1'
    step_id = 'analytics'
    setup_tool.runImportStepFromProfile(profile_id, step_id)


def upgrade_10b1_to_10b2(setup_tool):
    """
    Update Analytics tool to use new properties.
    """

    analytics_tool = getToolByName(setup_tool, 'portal_analytics')

    if hasattr(analytics_tool, 'email'):
        del analytics_tool.email

    if hasattr(analytics_tool, 'password'):
        del analytics_tool.password

    if hasattr(analytics_tool, 'profile'):
        del analytics_tool.profile

    if not hasattr(analytics_tool, 'auth_token'):
        analytics_tool.auth_token = None

    if not hasattr(analytics_tool, 'tracking_web_property'):
        analytics_tool.tracking_web_property = None

    if not hasattr(analytics_tool, 'tracking_plugin_names'):
        analytics_tool.tracking_plugin_names = []

    if not hasattr(analytics_tool, 'reports_profile'):
        analytics_tool.reports_profile = None

    OLD_ROWS = "python:[str(row[date_range_dimension]), int(float(metric('ga:timeOnSite', row))/float(metric('ga:visits', row)))]"
    NEW_ROWS = "python:[str(row[date_range_dimension]), int(float(metric('ga:timeOnSite', row))/(float(metric('ga:visits', row)) + .0001))]"

    if 'site-timeonsite-line' in analytics_tool.objectIds():
        report = analytics_tool['site-timeonsite-line']
        if report.rows == OLD_ROWS:
            report.rows = NEW_ROWS


def upgrade_10b3_to_10(setup_tool):
    """
    Add icon expression in Plone 4.
    """

    name = 'profile-collective.googleanalytics:upgrade_10b3_10'
    setup_tool.runAllImportStepsFromProfile(name)


def upgrade_10_to_11(setup_tool):
    """
    Cleanup old stuff
    """

    analytics_tool = getToolByName(setup_tool, 'portal_analytics')

    if hasattr(analytics_tool, 'auth_token'):
        del analytics_tool.auth_token
    if hasattr(analytics_tool, '_v_temp_clients'):
        analytics_tool._v_temp_clients = None

    jar = analytics_tool._p_jar

    if hasattr(jar, 'foreign_connections'):
        delattr(jar, 'foreign_connections')


def upgrade_11_to_12(setup_tool):
    analytics_tool = getToolByName(setup_tool, 'portal_analytics')

    if analytics_tool._auth_token is None:
        ann = IAnnotations(analytics_tool)
        auth_token = ann.get('auth_token', None)
        if auth_token is not None:
            analytics_tool._auth_token = auth_token
            del ann['auth_token']
        valid_token = ann.get('valid_token', None)
        if valid_token is not None:
            analytics_tool._valid_token = valid_token
            del ann['valid_token']

    registry = getUtility(IRegistry)
    try:
        records = registry.forInterface(IAnalyticsSchema)
    except KeyError:
        registry.registerInterface(IAnalyticsSchema)
        records = registry.forInterface(IAnalyticsSchema)
        for field in IAnalyticsSchema:
            setattr(records, field,
                    getattr(analytics_tool, field,
                            IAnalyticsSchema[field].missing_value))


def upgrade_12_to_13(setup_tool):
    """
    Remove gdata record and install resource registry
    """

    name = 'profile-collective.googleanalytics:upgrade_12_13'
    setup_tool.runAllImportStepsFromProfile(name)

    analytics_tool = getToolByName(setup_tool, 'portal_analytics')
    # this will update the creds to use a dict instead. but if not it will be done on first access
    analytics_tool._get_credentials()
