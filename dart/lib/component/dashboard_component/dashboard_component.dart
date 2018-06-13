part of security_monkey;

@Component(
    selector: 'dashboard',
    templateUrl: 'packages/security_monkey/component/dashboard_component/dashboard_component.html',
    useShadowDom: false)
class DashboardComponent {
    List accounts;
    List technologies;
    List<Item> selectedItems;
    List<Issue> agingIssues;
    Map techScoreMap;
    Map accountScoreMap;
    RouteProvider routeProvider;
    Router router;
    ObjectStore store;
    bool accountsLoaded = false;
    bool technologySummaryLoaded = false;
    bool highScoreSummaryLoaded = false;
    bool agingIssueSummaryLoaded = false;
    bool selectAll = true;

    Map<String, String> accountFilterParams = {
        'page': '1',
        'active': true,
        'count': '1000000000' // This should retrieve all
    };

    Map<String, String> itemFilterParams = {
        'regions': '',
        'technologies': '',
        'accounts': '',
        'accounttypes': '',
        'names': '',
        'active': true,
        'searchconfig': null,
        'summary': true,
        'page': '1',
        'count': '1000000000' // This should retrieve all
    };

    Map<String, String> agingIssueFilterParams = {
        'regions': '',
        'technologies': '',
        'accounts': '',
        'accounttypes': '',
        'names': '',
        'active': null,
        'searchconfig': null,
        'justified': false,
        'enabledonly': 'true',
        'summary': true,
        'page': '1',
        'count': '10'
    };

    DashboardComponent(this.routeProvider, this.router, this.store) {
        store.list(Account, params: accountFilterParams).then((accountItems) {
            this.accounts = new List();
            this.selectedItems = new List();
            for (var accountItem in accountItems) {
                var account = new Map();
                account['selected_for_action'] = selectAll;
                account['id'] = accountItem.id;
                account['name'] = accountItem.name;
                account['items'] = new List();
                account['total_score'] = 0;
                this.accounts.add(account);
                fetchItems(account);
            }
            accountsLoaded = true;
            recalculateAgingIssueSummary();
        });
    }

    void fetchItems(account) {
        itemFilterParams['accounts'] = account['name'];
        store.list(Item, params: itemFilterParams).then((items) {
            account['items'] = items;
            if (account['selected_for_action']) {
                this.selectedItems = [this.selectedItems, account['items']].expand((x) => x).toList();
            }
            highScoreSummaryLoaded = true;
            recalculateSummaryScores();
        });
    }

    void recalculateSummaryScores() {
        technologySummaryLoaded = false;
        techScoreMap = new Map();
        accountScoreMap = new Map();
        for (var item in selectedItems) {
            // Add item score to technology map
            if (techScoreMap.containsKey(item.technology)) {
                techScoreMap[item.technology] = techScoreMap[item.technology] + item.unjustifiedScore();
            } else {
                techScoreMap[item.technology] = item.unjustifiedScore();
            }
            // Add item score to account score map
            if (accountScoreMap.containsKey(item.account)) {
                accountScoreMap[item.account] = accountScoreMap[item.account] + item.unjustifiedScore();
            } else {
                accountScoreMap[item.account] = item.unjustifiedScore();
            }
        }
        // angular.dart does not support iterating over hash map so convert to array
        technologies = new List();
        techScoreMap.forEach((k,v) {
            technologies.add({'name': k, 'score': v});
        });
        technologySummaryLoaded = true;

        // Update accounts['total_score'] after items have been parsed
        for (var account in accounts) {
            if (accountScoreMap.containsKey(account['name'])) {
                account['total_score'] = accountScoreMap[account['name']];
            }
        }
    }

    void recalculateAgingIssueSummary() {
        agingIssueSummaryLoaded = false;
        agingIssueFilterParams['accounts'] = selectedAccountsParam();

        store.list(Issue, params: agingIssueFilterParams).then((issues) {
            this.agingIssues = issues;
            this.agingIssueSummaryLoaded = true;
        });
    }

    void recalculateAllSummaries() {
        var selectedAccountsList = selectedAccounts();
        // Combine selected accounts items
        this.selectedItems = new List();
        for (var account in selectedAccountsList) {
            this.selectedItems = [this.selectedItems, account['items']].expand((x) => x).toList();
        }
        recalculateSummaryScores();
        recalculateAgingIssueSummary();
        // High Score Items is updated when selectedItems changes
    }

    String selectedAccountsParam() {
        var selectedAccountNamesList = selectedAccountNames();
        if (selectedAccountNamesList.length > 0) {
            return selectedAccountNamesList.join(',');
        } else {
            return 'NONE';
        }
    }

    List selectedAccounts() {
        var accountsArray = new List();
        for (var account in accounts) {
            if (account['selected_for_action']) {
                accountsArray.add(account);
            }
        }
        return accountsArray;
    }

    List selectedAccountNames() {
        var accountNamesArray = new List();
        for (var account in accounts) {
            if (account['selected_for_action']) {
                accountNamesArray.add(account['name']);
            }
        }
        return accountNamesArray;
    }

    String getAccountFilter() {
        var accountFilters = new List();
        for (var account in accounts) {
            if (account['selected_for_action']) {
                accountFilters.add(account['name']);
            }
        }

        if (accountFilters.length == accounts.length) {
            return '-';
        } else if (accountFilters.length > 0) {
            return accountFilters.join('%2C');
        } else {
            return 'None';
        }
    }

    void selectAllToggle() {
        selectAll = !selectAll;
        for (var account in accounts) {
            account['selected_for_action'] = selectAll;
        }
    }

    // Sorting
    var sort_params = {
        'account': {
            'sorting_column': 'total_score',
            'sort_asc': false,
            'sort_value': '-score'
        },
        'technology': {
            'sorting_column': 'score',
            'sorc_asc': false,
            'sort_value': '-score'
        }
    };

    void sortColumn(var table, var column) {
        if (sort_params[table]['sorting_column'] == column) {
            sort_params[table]['sort_asc'] = !sort_params[table]['sort_asc'];
            if (sort_params[table]['sort_asc']) {
                sort_params[table]['sort_value'] = column;
            } else {
                sort_params[table]['sort_value'] = '-' + column;
            }
        } else {
            sort_params[table]['sorting_column'] = column;
            sort_params[table]['sort_asc'] = true;
            sort_params[table]['sort_value'] = column;
        }
    }

    String classForColumn(var table, var column) {
        if (sort_params[table]['sorting_column'] == column) {
            if (sort_params[table]['sort_asc']) {
                return "glyphicon glyphicon glyphicon-sort-by-attributes";
            } else {
                return "glyphicon glyphicon glyphicon-sort-by-attributes-alt";
            }
        } else {
            return "glyphicon glyphicon-sort";
        }
    }
}
