odoo.define('omixtory.ListController', function(require) {
    "use strict";

var core = require('web.core');
var _t = core._t;
var session = require('web.session');
var framework = require('web.framework');
var Widget = require('web.Widget');
var Dialog = require('web.Dialog');
var ListController = require("web.ListController");

var myalert = function (owner, title, message, reload) {
    var buttons = [{
        text: "Ok",
        close: true,
        click: reload,
    }];
    return new Dialog(owner, _.extend({
        size: 'medium',
        buttons: buttons,
        $content: $('<main/>', {
            role: 'alert',
            text: message,
        }),
        title: title,
    })).open({shouldFocusButtons:true});
};

var MyWidget = Widget.extend({
    // the name of the QWeb template to use for rendering
    template: "ImportSelected",

    events: {
        // 'change .oe_import_grid input': 'import_dryrun',
        'change .oe_import_selected_file': function (e) {
            var self = this;
            var z = e.target;
            this.$el.ajaxSubmit({
                url: '/omixtory/import/selectedrows',
                complete: function (params) {
                    self.destroy()
                },
                success: function (params) {
                    var reload = function () {
                        self.parent.do_action('reload')
                    }
                    myalert(this, params['title'], params['message'], reload)
                },
                error: function (params) {
                    myalert(this, _("Error"), params.statusText)
                },
            });
        }
    },
    init: function (parent) {
        this._super.apply(this, arguments);
        this.parent = parent;
    },
    start: function() {
        // stuff you want to make after the rendering, `this.$el` holds a correct value
        var file = this.$("input.oe_import_selected_file")[0]
        file.click();
        return this._super.apply(this, arguments);
    }
});

var includeDict = {
    _onExportSelectedRows: function () {
        framework.blockUI();
        this.getSession().get_file({
            url: '/omixtory/export/selectedrows',
            model: this.modelName,
            ids: this.getSelectedIds(),
            data: {
                model: this.modelName,
                ids: this.getSelectedIds(),
            },
            complete: framework.unblockUI,
            error: function (params) {
                myalert(this, params['title'], params['message'])
            },
        });
    },
    _onImportSelectedRows: function () {
        var myWidget = new MyWidget(this);
        myWidget.appendTo($(".o_list_buttons"));

//        this._rpc({
//            route: '/omixtory/import/selectedrows',
//            params: {
//            },
//        }).then(function(params) {
//            myalert(this, params['title'], params['message'])
//        })
    },

    renderButtons: function ($node) {
        this._super.apply(this, arguments); // Possibly sets this.$buttons
        if (this.$buttons) {
            this.$buttons.on('click', '.o_button_import_selected', this._onImportSelectedRows.bind(this));
            this.$buttons.appendTo($node);
        }
    },

    renderSidebar: function ($node) {
        this._super.apply(this, arguments);
        if(this.sidebar){
            this.sidebar._addToolbarActions({other : [{
                label: _t("Export Selected Rows"),
                callback: this._onExportSelectedRows.bind(this)
            }]});
        }
    }
};

ListController.include(includeDict);
});
