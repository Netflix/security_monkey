$(document).ready(function() {

  $("#s2_regions").select2({

          placeholder: "",
          allowClear: true,
          blurOnChange: true,
          openOnEnter: false,
          multiple: true,
          ajax: {
            url: function() {
              return "/api/1/distinct/region?select2=True"+getFilterString();
            },
            params: {
              xhrFields: { withCredentials: true }
            },
            dataType: 'json',
            data: function (term, page) {
              return {
                page: page,
                count: 25,
                q: term
              };
            },
            results: function (data, page) {
              var more = (page * 25) < data.total;
              return { results: data.items, more: more };
            }
          },
          formatResult: namesformat,
          formatSelection: namesformat,
          escapeMarkup: function(m) { return m; },
          initSelection : function (element, callback) {
            var data = [];
            $(element.val().split(",")).each(function () {
                data.push({id: this, text: this});
            });
            callback(data);
          }
        });

  $('#s2_regions').on('change', function(e) {
    $('#filterregions').val(e.val);
    pushFilterRoutes();
  });

  $("#s2_technologies").select2({
        tags:["red", "green", "blue"],
        tokenSeparators: [",", " "],
        placeholder: "",
        allowClear: true,
        blurOnChange: true,
        openOnEnter: false,
        multiple: true,
        ajax: {
          url: function() {
            return "/api/1/distinct/tech?select2=True"+getFilterString();
          },
          params: {
            xhrFields: { withCredentials: true }
          },
          dataType: 'json',
          data: function (term, page) {
            return {
              page: page,
              count: 25,
              q: term
            };
          },
          results: function (data, page) {
            var more = (page * 25) < data.total;
            return { results: data.items, more: more };
          }
        },
        formatResult: namesformat,
        formatSelection: namesformat,
        escapeMarkup: function(m) { return m; },
        initSelection : function (element, callback) {
          var data = [];
          $(element.val().split(",")).each(function () {
              data.push({id: this, text: this});
          });
          callback(data);
        }
      });
  $('#s2_technologies').on('change', function(e) {
    $('#filtertechnologies').val(e.val);
    pushFilterRoutes();
  });

  $("#s2_accounts").select2({
      tags:["red", "green", "blue"],
      tokenSeparators: [",", " "],
      placeholder: "",
      allowClear: true,
      blurOnChange: true,
      openOnEnter: false,
      multiple: true,
      ajax: {
        url: function() {
          return "/api/1/distinct/account?select2=True"+getFilterString();
        },
        params: {
          xhrFields: { withCredentials: true }
        },
        dataType: 'json',
        data: function (term, page) {
          return {
            page: page,
            count: 25,
            q: term
          };
        },
        results: function (data, page) {
          var more = (page * 25) < data.total;
          return { results: data.items, more: more };
        }
      },
      formatResult: namesformat,
      formatSelection: namesformat,
      escapeMarkup: function(m) { return m; },
      initSelection : function (element, callback) {
        var data = [];
        $(element.val().split(",")).each(function () {
            data.push({id: this, text: this});
        });
        callback(data);
      }
    });
  $('#s2_accounts').on('change', function(e) {
    $('#filteraccounts').val(e.val);
    pushFilterRoutes();
  });

  // If the name is too long ( > 25 characters)
  // Insert a special character (&#8203;) every 25 characters
  // that will be invisible but will allow the name to wrap.
  function namesformat(state) {
    if (!state.id) return state.text; // optgroup
    var text = '';
    if (state.text.length > 25) {
      for(var i=0; i<state.text.length; i=i+25) {
        text = text +'&#8203;'+ state.text.substring(i, i+25);
      }
    } else {
      text = state.text;
    }
    // Required or we will only get the revision_id and not the actual text
    state.id=state.text;
    return text;
  }

  $("#s2_names").select2({
    tags:["red", "green", "blue"],
    tokenSeparators: [",", " "],
    placeholder: "",
    allowClear: true,
    blurOnChange: true,
    openOnEnter: false,
    multiple: true,
    ajax: {
      url: function() {
        return "/api/1/distinct/name?select2=True"+getFilterString();
      },
      params: {
        xhrFields: { withCredentials: true }
      },
      dataType: 'json',
      data: function (term, page) {
        return {
          page: page,
          count: 25,
          q: term
        };
      },
      results: function (data, page) {
        var more = (page * 25) < data.total;
        return { results: data.items, more: more };
      }
    },
    formatResult: namesformat,
    formatSelection: namesformat,
    escapeMarkup: function(m) { return m; },
    initSelection : function (element, callback) {
      var data = [];
      $(element.val().split(",")).each(function () {
          data.push({id: this, text: this});
      });
      callback(data);
    }
  });

  $('#s2_names').on('change', function(e) {
    $('#filternames').val(e.val);
    pushFilterRoutes();
  });

});