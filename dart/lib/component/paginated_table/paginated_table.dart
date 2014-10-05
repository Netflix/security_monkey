part of security_monkey;

abstract class PaginatedTable {
    Scope scope;
    bool is_error = false;
    bool is_loaded = false;
    String err_message = "";

    PaginatedTable();

    void setupTable(Scope scope) {
        this.scope = scope;
        scope.on("globalAlert").listen(this._showErrorMessage);
    }

    void _showErrorMessage(ScopeEvent event) {
        this.is_error = true;
        this.err_message = event.data;
    }

    void setPaginationData(Map paginationData) {
        this.totalItems = paginationData['total'];
        this.actualCount = paginationData['count'] != null ? paginationData['count'] : 25;
        print("Setting totalitems to $totalItems");
        print("Setting actualCount to $actualCount");
    }

    void list() {
        print("listFunction should be overridden");
    }

    /* PAGINATION BEGIN */
    int totalItems;
    int actualCount = 0;
    int _currentPage = 1;
    int maxSize = 5; // Max number of pages to display

    pageChanged() => null;

    get currentPage => _currentPage;
    set currentPage(int newPage) {
        if (_currentPage != newPage) {
            _currentPage = newPage;
            list();
        }
    }

    String items_displayed() {
        // return 1-25 or 26-27
        int start = (currentPage - 1) * _items_per_page + 1;
        int end = start + actualCount - 1;
        if (start > end) {
            return "$end";
        }
        if (end > totalItems) {
            print("Calculated an end higher than the total. Start: $start Count: $actualCount End: $end");
            return "$start-$totalItems";
        }
        return "$start-$end";
    }

    List<String> items_per_page_options = ['10', '25', '50', '100', '250', '1000'];

    int _items_per_page = 25;
    get ipp_as_int => _items_per_page;
    get items_per_page => _items_per_page.toString();
    set items_per_page(ipp) {
        ipp = int.parse(ipp);
        if (ipp != _items_per_page) {
            _items_per_page = ipp;
            list();
        }
    }
    /* PAGINATION END */
}
