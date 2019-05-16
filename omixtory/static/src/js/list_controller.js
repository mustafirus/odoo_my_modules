odoo.define('omixtory.ListController', function(require) {
    "use strict";

var core = require('web.core');
var _t = core._t;

var ListController = require("web.ListController");

var includeDict = {
    _onExportSelectedRows: function () {
        this._rpc({
            route: '/omixtory/export/selectedrows',
            params: {
                model: this.modelName,
                ids: this.getSelectedIds(),
            },
        })
    },
    _onImportSelectedRows: function () {
        this._rpc({
            route: '/omixtory/import/selectedrows',
            params: {
            },
        })
    },

    renderSidebar: function ($node) {
        this._super.apply(this, arguments);
        if(this.sidebar){
            this.sidebar._addToolbarActions({other : [{
                label: _t("Export Selected Rows"),
                callback: this._onExportSelectedRows.bind(this)
            }]});
            this.sidebar._addToolbarActions({other : [{
                label: _t("Import Selected Rows"),
                callback: this._onImportSelectedRows.bind(this)
            }]});
        }
    }
};

ListController.include(includeDict);
});
