#!/usr/bin/env python

import datetime
import math
import pkg_resources

from genshi.builder import tag
from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
                            add_script, add_script_data
from trac.perm import IPermissionRequestor
from trac.util.datefmt import to_utimestamp, utc
from trac.util.translation import _

class TicketGraphModule(Component):
    implements(IPermissionRequestor, IRequestHandler, INavigationContributor, ITemplateProvider)

    # IPermissionRequestor methods
    def get_permission_actions(self):
        return [ 'TICKET_GRAPH' ]

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'ticketgraph'

    def get_navigation_items(self, req):
        if 'TICKET_GRAPH' in req.perm:
            yield ('mainnav', 'ticketgraph',
                   tag.a(_('Ticket Graph'), href=req.href.ticketgraph()))

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [ ('ticketgraph', pkg_resources.resource_filename(__name__, 'htdocs')) ]

    def get_templates_dirs(self):
        return [ pkg_resources.resource_filename(__name__, 'templates') ]

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/ticketgraph'

    def process_request(self, req):
        req.perm.require('TICKET_GRAPH')

        today = datetime.datetime.combine(datetime.date.today(), datetime.time(tzinfo=utc))

        days = int(req.args.get('days', 30))
        owner = req.args.get('owner', "%")
        stack_graph={};
        stack_graph['stack_graph'] = bool(int(req.args.get('sg', 0)))
        # These are in microseconds; the data returned is in milliseconds
        # because it gets passed to flot
        ts_start = to_utimestamp(today - datetime.timedelta(days=days))
        ts_end = to_utimestamp(today) + 86400000000;
        ts_utc_delta = math.ceil((datetime.datetime.utcnow()-datetime.datetime.now()).total_seconds())*1000;

        db = self.env.get_read_db()
        cursor = db.cursor()

        series = {
            'openedTickets': {},
            'closedTickets': {},
            'workedTickets': {},
            'reopenedTickets': {},
            'openTickets': {}
        }
        args = [ts_start, ts_end];
        tix_args = [ts_start, ts_end];
        where = '';
        tix_where = '';
        if owner=="" :
                owner = "%"

        if owner!="%" :
                where += 'AND author LIKE %s ';
                tix_where += 'AND reporter LIKE %s ';
                args.append(owner)
                tix_args.append(owner)


        # number of created tickets for the time period, grouped by day (ms)
        cursor.execute('SELECT COUNT(DISTINCT id),( UNIX_TIMESTAMP(DATE(FROM_UNIXTIME(time/1000000)))*1000) ' \
                       'AS date FROM ticket WHERE time BETWEEN %s AND %s ' + tix_where +
                       'GROUP BY date ORDER BY date ASC', tix_args)
        for count, timestamp in cursor:
            series['openedTickets'][float(timestamp)] = float(count)

        # number of reopened tickets for the time period, grouped by day (ms)
        cursor.execute('SELECT COUNT(DISTINCT ticket), UNIX_TIMESTAMP(DATE(FROM_UNIXTIME(time/1000000)))*1000 ' \
                       'AS date FROM ticket_change WHERE field = \'status\' AND newvalue = \'reopened\' ' \
                       'AND time BETWEEN %s AND %s ' + where +
                       'GROUP BY date ORDER BY date ASC', args)
        for count, timestamp in cursor:
            series['reopenedTickets'][float(timestamp)] = float(count)

        # number of worked tickets for the time period, grouped by day (ms)
        cursor.execute('SELECT COUNT(DISTINCT ticket), UNIX_TIMESTAMP(DATE(FROM_UNIXTIME(time/1000000)))*1000 ' \
                       'AS date FROM ticket_change WHERE  ' \
                       'time BETWEEN %s AND %s ' + where +
                       'GROUP BY date ORDER BY date ASC', args)
        for count, timestamp in cursor:
            series['workedTickets'][float(timestamp)] = float((1 if stack_graph['stack_graph'] else -1)*count)


        # number of closed tickets for the time period, grouped by day (ms)
        cursor.execute('SELECT COUNT(DISTINCT ticket), UNIX_TIMESTAMP(DATE(FROM_UNIXTIME(time/1000000)))*1000 ' \
                       'AS date FROM ticket_change WHERE field = \'status\' AND newvalue = \'closed\' ' \
                       'AND time BETWEEN %s AND %s ' + where +
                       'GROUP BY date ORDER BY date ASC', args)
        for count, timestamp in cursor:
            series['closedTickets'][float(timestamp)] = float((1 if stack_graph['stack_graph'] else -1)*count)

        # number of open tickets at the end of the reporting period
        if owner!='%' :
                cursor.execute('SELECT COUNT(*) FROM ticket WHERE status <> \'closed\' AND owner LIKE %s ', [owner])
        else:
                cursor.execute('SELECT COUNT(*) FROM ticket WHERE status <> \'closed\' ')


        open_tickets = cursor.fetchone()[0]
        open_ts = math.floor((ts_end) / 1000)+ts_utc_delta

#        series['openTickets'][open_ts] = open_tickets

        while open_ts >= math.floor(ts_start / 1000):
            if open_ts in series['closedTickets']:
                open_tickets += (1 if stack_graph['stack_graph'] else -1)*series['closedTickets'][open_ts]
            if open_ts in series['openedTickets']:
                open_tickets -= series['openedTickets'][open_ts]
            if open_ts in series['reopenedTickets']:
                open_tickets -= series['reopenedTickets'][open_ts]

            series['openTickets'][open_ts-86400000] = open_tickets

            new_ts_utc_delta = math.ceil((datetime.datetime.utcfromtimestamp(open_ts/1000)-datetime.datetime.fromtimestamp(open_ts/1000)).total_seconds())*1000;

            open_ts -= 86400000 + ts_utc_delta - new_ts_utc_delta
            ts_utc_delta = new_ts_utc_delta

        data = {}
        for i in series:
            keys = series[i].keys()
            keys.sort()
            data[i] = [ (k, series[i][k]) for k in keys ]

        data['owner'] = owner
        data['users']={}
        i=0;
        for user in self.env.get_known_users():
                data['users'][i] = user
                i=i+1

        add_script(req, 'ticketgraph/jquery.flot.min.js')
#        add_script(req, 'http://people.iola.dk/olau/flot/jquery.flot.js')
        add_script(req, 'ticketgraph/jquery.flot.stack.min.js')
        add_script(req, 'ticketgraph/ticketgraph.js')
        add_script_data(req, data)
        add_script_data(req, stack_graph)

        return 'ticketgraph.html', { 'days': days, 'sg': stack_graph['stack_graph'] }, None
