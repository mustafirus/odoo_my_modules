odoo.define('omixtory.ListController', function(require) {
    "use strict";

var core = require('web.core');
var _t = core._t;
var Dialog = require('web.Dialog');
var framework = require('web.framework');
var pyUtils = require('web.py_utils');
var crash_manager = require('web.crash_manager');

var ListController = require("web.ListController");
var myalert = function (owner, title, message, options) {
    var buttons = [{
        text: "Ok",
        close: true,
        click: options && options.confirm_callback,
    }];
    return new Dialog(owner, _.extend({
        size: 'medium',
        buttons: buttons,
        $content: $('<main/>', {
            role: 'alert',
            text: message,
        }),
        title: title,
    }, options)).open({shouldFocusButtons:true});
};

var includeDict = {
    _onExportSelectedRows: function () {
//        this._rpc({
//            route: '/omixtory/export/selectedrows',
//            params: {
//                model: this.modelName,
//                ids: this.getSelectedIds(),
//            },
//        }).then(function(params) {
//            myalert(this, params['title'], params['message'])
//        })

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
//                crash_manager.rpc_error.apply(crash_manager, arguments);
            },
        });
    },
    _onImportSelectedRows: function () {
        this._rpc({
            route: '/omixtory/import/selectedrows',
            params: {
            },
        }).then(function(params) {
            myalert(this, params['title'], params['message'])
        })
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
/*
            this.sidebar._addToolbarActions({other : [{
                label: _t("Import Selected Rows"),
                callback: this._onImportSelectedRows.bind(this)
            }]});
*/
        }
    }
};

ListController.include(includeDict);
});
