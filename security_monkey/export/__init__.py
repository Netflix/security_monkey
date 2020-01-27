from flask import request, Response
from flask.blueprints import Blueprint
from sqlalchemy.sql.expression import cast
from sqlalchemy import String, or_
from security_monkey import rbac
from security_monkey.datastore import Item, ItemRevision, Account, Technology, ItemAudit, AuditorSettings
from sqlalchemy.orm import joinedload


export_blueprint = Blueprint("export", __name__)


@export_blueprint.route("/export/items")
@rbac.allow(roles=["View"], methods=["GET"])
def export_items():
    args = {}
    args['regions'] = request.args.get('regions', None)
    args['accounts'] = request.args.get('accounts', None)
    args['active'] = request.args.get('active', None)
    args['names'] = request.args.get('names', None)
    args['technologies'] = request.args.get('technologies', None)
    args['searchconfig'] = request.args.get('searchconfig', None)
    args['ids'] = request.args.get('ids', None)

    for k, v in list(args.items()):
        if not v:
            del args[k]

    query = Item.query.join((ItemRevision, Item.latest_revision_id == ItemRevision.id))
    if 'regions' in args:
        regions = args['regions'].split(',')
        query = query.filter(Item.region.in_(regions))
    if 'accounts' in args:
        accounts = args['accounts'].split(',')
        query = query.join((Account, Account.id == Item.account_id))
        query = query.filter(Account.name.in_(accounts))
    if 'technologies' in args:
        technologies = args['technologies'].split(',')
        query = query.join((Technology, Technology.id == Item.tech_id))
        query = query.filter(Technology.name.in_(technologies))
    if 'names' in args:
        names = args['names'].split(',')
        query = query.filter(Item.name.in_(names))
    if 'ids' in args:
        ids = args['ids'].split(',')
        query = query.filter(Item.id.in_(ids))
    if 'active' in args:
        active = args['active'].lower() == "true"
        query = query.filter(ItemRevision.active == active)
    if 'searchconfig' in args:
        searchconfig = args['searchconfig']
        query = query.filter(cast(ItemRevision.config, String).ilike('%{}%'.format(searchconfig)))

    # Eager load the joins and leave the config column out of this.
    query = query.options(joinedload('issues'))
    # Now loaded by the join on line 29 I think...
    #query = query.options(joinedload('revisions').defer('config'))
    query = query.options(joinedload('account'))
    query = query.options(joinedload('technology'))

    query = query.order_by(ItemRevision.date_created.desc())
    attributes = [
        ["technology", "name"],
        ["account", "name"],
        ["account", "identifier"],
        ["region"],
        ["name"],
        ["issues"],
        ["comments"]
    ]

    out = ",".join(["/".join(at) for at in attributes]) + "\n"

    for item in query:
        values = []
        for attribute in attributes:
            val = item
            for at in attribute:
                val = getattr(val, at)
                if val is None:
                    break
            val = str(val).replace('"', '""')
            values.append('"{val}"'.format(val=val))

        out += ",".join(values) + "\n"
    return Response(out, mimetype='text/csv',
                    headers={"Content-disposition": "attachment; filename=security-monkey-items.csv"})


@export_blueprint.route("/export/issues")
@rbac.allow(roles=["View"], methods=["GET"])
def export_issues():
    args = {}
    args['regions'] = request.args.get('regions', None)
    args['accounts'] = request.args.get('accounts', None)
    args['active'] = request.args.get('active', None)
    args['names'] = request.args.get('names', None)
    args['technologies'] = request.args.get('technologies', None)
    args['searchconfig'] = request.args.get('searchconfig', None)
    args['ids'] = request.args.get('ids', None)

    for k, v in list(args.items()):
        if not v:
            del args[k]

    query = ItemAudit.query.join("item")
    query = query.filter(ItemAudit.fixed == False)
    if 'regions' in args:
        regions = args['regions'].split(',')
        query = query.filter(Item.region.in_(regions))
    if 'accounts' in args:
        accounts = args['accounts'].split(',')
        query = query.join((Account, Account.id == Item.account_id))
        query = query.filter(Account.name.in_(accounts))
    if 'technologies' in args:
        technologies = args['technologies'].split(',')
        query = query.join((Technology, Technology.id == Item.tech_id))
        query = query.filter(Technology.name.in_(technologies))
    if 'names' in args:
        names = args['names'].split(',')
        query = query.filter(Item.name.in_(names))
    if 'active' in args:
        active = args['active'].lower() == "true"
        query = query.join((ItemRevision, Item.latest_revision_id == ItemRevision.id))
        query = query.filter(ItemRevision.active == active)
    if 'searchconfig' in args:
        search = args['searchconfig'].split(',')
        conditions = []
        for searchterm in search:
            conditions.append(ItemAudit.issue.ilike('%{}%'.format(searchterm)))
            conditions.append(ItemAudit.notes.ilike('%{}%'.format(searchterm)))
            conditions.append(ItemAudit.justification.ilike('%{}%'.format(searchterm)))
            conditions.append(Item.name.ilike('%{}%'.format(searchterm)))
        query = query.filter(or_(*conditions))
    if 'enabledonly' in args:
        query = query.join((AuditorSettings, AuditorSettings.id == ItemAudit.auditor_setting_id))
        query = query.filter(AuditorSettings.disabled == False)

    query = query.order_by(ItemAudit.justified, ItemAudit.score.desc())

    attributes = [
        ["item", "technology", "name"],
        ["item", "account", "name"],
        ["item", "account", "identifier"],
        ["item", "region"],
        ["item", "name"],
        ["item", "comments"],
        ["score"],
        ["issue"],
        ["notes"],
        ["justified"],
        ["user", "email"],
        ["justification"]
    ]

    out = ",".join(["/".join(at) for at in attributes]) + "\n"

    for issue in query:
        values = []
        for attribute in attributes:
            val = issue
            for at in attribute:
                val = getattr(val, at)
                if val is None:
                    break
            val = str(val).replace('"', '""')
            values.append('"{val}"'.format(val=val))

        out += ",".join(values) + "\n"
    return Response(out, mimetype='text/csv',
                    headers={"Content-disposition": "attachment; filename=security-monkey-items.csv"})
