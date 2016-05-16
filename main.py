#!/usr/bin/env python
import random
import json

from flask import Flask, Response, request
from werkzeug.contrib.cache import SimpleCache
from jira import JIRA

jira = JIRA('https://jira.atlassian.com')


app = Flask(__name__)
cache = SimpleCache()


@app.route("/")
def index():
    return app.send_static_file('index.html')


"""
Method	URI	                                     Action
GET	http://[hostname]/api/v0/tickets	     Retrieve list of tickets
GET	http://[hostname]/api/v0/tickets/[ticket_id] Retrieve a ticket
POST	http://[hostname]/api/v0/tickets	     Create a new ticket
PUT	http://[hostname]/api/v0/tickets/[ticket_id] Update an existing ticket
DELETE	http://[hostname]/api/v0/tickets/[ticket_id] Delete a ticket
"""
FIELDS = ['summary', 'description', 'labels', 'components', 'assignee']


def jira_query(jql):
    tickets = cache.get(jql)
    if tickets:
        print "HIT: {0}".format(jql)
        return tickets

    print "SLOW ASS JQL: {0}".format(jql)
    results = jira.search_issues(jql, maxResults=30, fields=FIELDS)
    tickets = [ticket.raw for ticket in results]
    cache.set(jql, tickets, timeout=5 * 60)

    return tickets


def js(data):
    return Response(json.dumps(data),  mimetype='application/json')


def upsert(data, key=None):
    key = 'TEST-{0}'.format(random.randint(0, 1000))
    key = data.get('key', key)
    data['key'] = key
    return data


@app.route('/api/v0/labels', methods=['GET'])
def GET_labels():
    labels = [
        {'name': 'GCN', 'class': 'btn-danger', 'map': 'gcn'},
        {'name': 'Iris', 'class': 'btn-danger', 'map': 'iris'},
        {'name': 'Manager', 'class': 'btn-warning', 'map': 'manager'},
        {'name': 'LIX', 'class': 'btn-warning', 'map': 'lix'},
        {'name': 'Proactive', 'class': 'btn-success', 'map': 'uplift'},
        {'name': 'Alert Cleanup', 'class': 'btn-success', 'map': 'cleanup'},

        {'name': 'Project', 'class': 'btn-success', 'map': 'project'}
    ]
    return js(labels)


@app.route('/api/v0/fabricgroups', methods=['GET'])
def GET_fabricgroups():
    fabricgroups = "prod ei dev".split()
    return js(fabricgroups)


@app.route('/api/v0/sizes', methods=['GET'])
def GET_sizes():
    labels = 'S M L'.split()
    return js(labels)


@app.route('/api/v0/tickets/', methods=['GET'])
def GET_tickets():
    print "GET_tickets", request.method
    jql = request.args.get('jql')
    tickets = jira_query(jql)
    return js(tickets)


@app.route('/api/v0/tickets/<ticket_id>/', methods=['GET'])
def GET_ticket(ticket_id):
    print "GET_tickets/<>", request.method
    jql = "KEY = {0}".format(ticket_id)
    ticket = jira_query(jql)[0]
    return js(ticket)


@app.route('/api/v0/tickets/', methods=['POST'])
def POST_ticket():
    """ Create a NEW ticket
    """
    print request.data
    data = json.loads(request.data)
    new_issue = jira.create_issue(
        project="JRA",
        summary=data.get('summary'),
        issuetype={'name': 'Bug'},
        description=data.get('description')
    )
    return js(new_issue), 201


@app.route('/api/v0/tickets/<ticket_id>/', methods=['PUT'])
def PUT_ticket(ticket_id):
    """ Update a ticket with <ticket_id>
    """
    data = json.loads(request.data)
    response = upsert(data)
    return js(response), 201


if __name__ == "__main__":
    app.run(debug=True)
