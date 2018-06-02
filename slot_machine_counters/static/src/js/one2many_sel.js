odoo.define('slot_machine_counters.one2many_sel', function (require) {
"use strict";


var core = require('web.core');

//var form_relational = require('web.form_relational');
var common = require('web.form_common');
var data = require('web.data');

var _t = core._t;

var One2ManyListView = core.one2many_view_registry.get('list');
var One2ManyListViewSel = One2ManyListView.extend({
    do_add_record: function () {
        var self = this;

        new common.SelectCreateDialog(this, {
            res_model: this.model,
            domain: new data.CompoundDomain(this.x2m.build_domain(), ["!", ["id", "in", this.x2m.dataset.ids]]),
            context: this.x2m.build_context(),
            title: _t("Add: ") + this.x2m.string,
            alternative_form_view: this.x2m.field.views ? this.x2m.field.views.form : undefined,
            no_create: this.x2m.options.no_create || !this.is_action_enabled('create'),
            on_selected: function(element_ids) {
                return self.x2m.data_link_multi(element_ids).then(function() {
                    self.x2m.reload_current_view();
                });
            }
        }).open();
    },
});


var FieldOne2Many = core.form_widget_registry.get('one2many');
var FieldOne2ManySel = FieldOne2Many.extend({
    init: function() {
        this._super.apply(this, arguments);
        this.x2many_views = {
            kanban: core.view_registry.get('one2many_kanban'),
            list: One2ManyListViewSel,
        };
    },
});


//var FieldOne2Many_Select = form_relational.FieldOne2Many/*.extend({})*/
/*
var FieldOne2Many_Select = form_relational.FieldOne2Many.extend({

    init: function () {
        alert("Hello! second I am an alert box!!");
    }


    do_add_record: function () {
        var self = this;

        new common.SelectCreateDialog(this, {
            res_model: this.model,
            domain: new data.CompoundDomain(this.x2m.build_domain(), ["!", ["id", "in", this.x2m.dataset.ids]]),
            context: this.x2m.build_context(),
            title: _t("Add: ") + this.x2m.string,
            alternative_form_view: this.x2m.field.views ? this.x2m.field.views.form : undefined,
            no_create: this.x2m.options.no_create || !this.is_action_enabled('create'),
            on_selected: function(element_ids) {
                return self.x2m.data_link_multi(element_ids).then(function() {
                    self.x2m.reload_current_view();
                });
            }
        }).open();
    },

});
*/

core.form_widget_registry.add(
    'one2many_sel', FieldOne2ManySel);


return {
    FieldOne2ManySel: FieldOne2ManySel,
}

});
