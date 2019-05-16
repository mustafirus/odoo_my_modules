odoo.define('omixtory.integer', function (require) {
"use strict";


//var core = require('web.core');

//var form_relational = require('web.form_relational');
//var common = require('web.form_common');
//
//var data = require('web.data');
var basic_fields = require('web.basic_fields');

//var _t = core._t;

var FieldInteger = basic_fields.FieldInteger.extend({
    _formatValue: function (value) {
        if (this.nodeOptions.wothsep) {
            return _.str.sprintf('%d', value);
        }
        return this._super.apply(this, arguments);
    },
});

var registry = require('web.field_registry');

registry
    .add('integer', FieldInteger)

return {
    FieldInteger: FieldInteger,
}

});
