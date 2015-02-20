part of security_monkey;

abstract class PaginatedTable implements ScopeAware {
    bool is_error = false;
    bool is_loaded = false;
    String err_message = "";

    PaginatedTable() {}

    void set scope(Scope scope) {
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

    /// PAGINATION BEGIN
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

    /// return 1-25 or 26-27
    String items_displayed() {
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
    /// PAGINATION END

    /// COLUMN SORTING
    String sorting_column = "none";
    bool sort_asc = true;

    void sort_column(var column) {
        if (sorting_column == column) {
            sort_asc = !sort_asc;
        } else {
            sorting_column = column;
            sort_asc = true;
        }
        list();
    }

    String order_dir() {
        if (sort_asc) return "Asc";
        return "Desc";
    }

    String class_for_column(var column) {
        if (sorting_column == column) {
            if (sort_asc) {
                return "glyphicon glyphicon-sort-by-alphabet";
            } else {
                return "glyphicon glyphicon-sort-by-alphabet-alt";
            }
        } else {
            return "glyphicon glyphicon-sort";
        }
    }
    /// COLUMN SORTING END
}
