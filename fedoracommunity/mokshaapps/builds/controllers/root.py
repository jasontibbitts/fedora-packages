# This file is part of Fedora Community.
# Copyright (C) 2008-2009  Red Hat, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from tg import expose, tmpl_context
from koji import BUILD_STATES

from paste.deploy.converters import asbool

from moksha.lib.base import Controller
from moksha.lib.helpers import Category, MokshaApp, not_anonymous, MokshaWidget
from moksha.api.widgets import ContextAwareWidget, Grid
from moksha.api.widgets.containers import DashboardContainer
from moksha.api.widgets.containers.dashboardcontainer import applist_widget

from fedoracommunity.widgets import SubTabbedContainer
from links import builds_links_group, builds_links, my_builds_links

import simplejson as json

class BuildsGrid(Grid, ContextAwareWidget):
    template='mako:fedoracommunity.mokshaapps.builds.templates.table_widget'
    params=['table_class']
    resource='koji'
    resource_path='query_builds'
    table_class=''

class BuildsPackagesGrid(Grid, ContextAwareWidget):
    template = 'mako:fedoracommunity.mokshaapps.builds.templates.packages_table_widget'
    resource = 'koji'
    resource_path = 'query_packages'


in_progress_builds_app = MokshaApp('In-progress Builds', 'fedoracommunity.builds/table',
                                       css_class='main_table',
                                       content_id='inprogress',
                                       params={'rows_per_page': 10,
                                               'show_title': True,
                                               'filters':{'state':BUILD_STATES['BUILDING'],
                                                          'profile': False,
                                                          'username': None
                                                         }
                                              })

failed_builds_app = MokshaApp('Failed Builds', 'fedoracommunity.builds/table',
                                       css_class='secondary_table',
                                       content_id='failed',
                                       params={'rows_per_page': 10,
                                               'show_title': True,
                                               'filters':{'state':BUILD_STATES['FAILED'],
                                                          'profile': False,
                                                          'username': None
                                                         }
                                              })

successful_builds_app = MokshaApp('Successful Builds', 'fedoracommunity.builds/table',
                                       css_class='secondary_table',
                                       content_id='successful',
                                       params={'rows_per_page': 10,
                                               'show_title': True,
                                               'filters':{'state':BUILD_STATES['COMPLETE'],
                                                          'profile': False,
                                                          'username': None,
                                                          'query_updates': True,
                                                         }
                                              })

overview_builds_app = MokshaApp('Overview',
                                 'fedoracommunity.builds/overview',
                                 content_id='builds_overview',
                                 params={'profile': False,
                                         'username': None})

class BuildsNavContainer(SubTabbedContainer):
    params = ['applist_widget']
    applist_widget = applist_widget
    template='mako:fedoracommunity.mokshaapps.builds.templates.builds_nav'
    sidebar_apps = (MokshaApp('Alerts', 'fedoracommunity.alerts', css_class='app panel'),
                    MokshaWidget('Tasks', 'fedoracommunity.quicklinks', css_class="app panel", auth=not_anonymous()))
    tabs = (Category('Packages I Own',
                     (overview_builds_app.clone({'profile': True},
                                                content_id='my_builds_overview'),
                      in_progress_builds_app.clone({'filters': {'profile': True}},
                                                   content_id='my_inprogress'),
                      failed_builds_app.clone({'filters': {'profile': True}},
                                                   content_id='my_failed'),
                      successful_builds_app.clone({'filters': {'profile': True}},
                                                   content_id='my_successful'),
                     ),
                     auth=not_anonymous()),
            Category('All Packages',
                     (overview_builds_app,
                      in_progress_builds_app,
                      failed_builds_app,
                      successful_builds_app)
                    )
           )

    def update_params(self, d):
        d['sidebar_apps'] = Category('sidebar-apps', self.sidebar_apps).process(d)

        super(BuildsNavContainer, self).update_params(d)

builds_nav_container = BuildsNavContainer('builds_nav')

builds_grid = BuildsGrid('builds_table')
builds_packages_grid = BuildsPackagesGrid('builds_packages_table')

class BuildsOverviewContainer(DashboardContainer, ContextAwareWidget):
    template = 'mako:fedoracommunity.mokshaapps.builds.templates.builds_overview_container'
    layout = [Category('group-1-apps',
                        (in_progress_builds_app.clone({'rows_per_page': 5,
                                                       'more_link_code': builds_links.IN_PROGRESS.code,
                                                       'show_title': False}),
                        failed_builds_app.clone({'rows_per_page': 5,
                                                 'more_link_code': builds_links.FAILED.code,
                                                 'show_title': False
                                                }))
                      ),
              Category('group-2-apps',
                       successful_builds_app.clone({'rows_per_page': 5,
                                                    'more_link_code': builds_links.SUCCESSFUL.code,
                                                    'show_title': False
                                                   })
                      )
             ]

builds_overview_container = BuildsOverviewContainer('builds_overview')

class MyBuildsOverviewContainer(DashboardContainer, ContextAwareWidget):
    template = 'mako:fedoracommunity.mokshaapps.builds.templates.builds_overview_container'
    layout = [Category('group-1-apps',
                        (in_progress_builds_app.clone({'rows_per_page': 5,
                                                       'more_link_code': my_builds_links.IN_PROGRESS.code,
                                                       'show_title': False
                                                      }),
                        failed_builds_app.clone({'rows_per_page': 5,
                                                 'more_link_code': my_builds_links.FAILED.code,
                                                 'show_title': False
                                                }))
                      ),
              Category('group-2-apps',
                       successful_builds_app.clone({'rows_per_page': 5,
                                                    'more_link_code': my_builds_links.SUCCESSFUL.code,
                                                    'show_title': False
                                                   })
                      )
             ]

my_builds_overview_container = MyBuildsOverviewContainer('my_builds_overview')

class RootController(Controller):

    @expose('mako:moksha.templates.widget')
    def index(self, **kwds):
        options = {}

        tmpl_context.widget = builds_nav_container
        return {'options':options}

    @expose('mako:moksha.templates.widget')
    def overview(self, profile=False, username=None, ):
        profile = asbool(profile)
        if profile:
            options = {'profile': profile}
            tmpl_context.widget = my_builds_overview_container
        else:
            options = {'username': username}
            tmpl_context.widget = builds_overview_container

        return {'options':options}

    @expose('mako:moksha.templates.widget')
    def name(self, pkg_name, **kwds):

        kwds.update({'p': pkg_name})
        return self.index(**kwds)

    @expose('mako:moksha.templates.widget')
    def packages_table(self, uid="", rows_per_page=5, filters=None, more_link_code=None):
        if isinstance(rows_per_page, basestring):
            rows_per_page = int(rows_per_page)

        if filters == None:
            filters = {}

        more_link = None
        if more_link_code:
            more_link = builds_links.get_data(more_link_code)
        else:
            alphaPager = numericPager = True

        tmpl_context.widget = builds_packages_grid
        return {'options':
                {'alphaPager': alphaPager,
                'numericPager': numericPager,
                'filters': filters,
                'rows_per_page':rows_per_page,
                'more_link': more_link}
               }

    @expose('mako:fedoracommunity.mokshaapps.builds.templates.table_container')
    def table(self,
              rows_per_page=5,
              filters=None,
              more_link_code=None,
              show_owner_filter=False,
              show_title=False):
        ''' table handler

        This handler displays the main table by itself
        '''

        title = ''

        if isinstance(rows_per_page, basestring):
            rows_per_page = int(rows_per_page)


        if filters == None:
            filters = {}

        decoded_filters=filters
        if isinstance(filters, basestring):
            # no point re-encoding so we will decode to a temp variable
            decoded_filters = json.loads(filters)

        if asbool(show_title):
            state = decoded_filters.get('state')
            if state == BUILD_STATES['FAILED']:
                title = 'Failed Builds: '
            elif state == BUILD_STATES['BUILDING']:
                title = 'In-progress Builds: '
            elif state == BUILD_STATES['COMPLETE']:
                title = 'Finished Builds: '

            profile = decoded_filters.get('profile')
            user = decoded_filters.get('username')
            if profile:
                title += "Packages I Own"
            elif user:
                title += "Packages " + username + " Owns"
            else:
                title += "All Packages"


        more_link = None
        numericPager = False
        if more_link_code:
            more_link = builds_links_group[more_link_code]
        else:
            numericPager = True


        state = decoded_filters.get('state')
        table_class = ''
        if not state:
            table_class = 'mixed-builds-table'
        elif state == BUILD_STATES['FAILED']:
            table_class = 'failed-builds-table'

        tmpl_context.widget = builds_grid

        return {'options':{'filters': filters,
                           'rows_per_page':rows_per_page,
                           'more_link': more_link,
                           'numericPager': numericPager,
                           'show_owner_filter': show_owner_filter,
                           'table_class': table_class},
                'title': title
               }
