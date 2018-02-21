<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="/">
    <odoo>
        <xsl:apply-templates select="form"/>
    </odoo>
  </xsl:template>

  <xsl:template match="form">
    <record id="view_subscription_form" model="ir.ui.view">
        <field name="name"><xsl:value-of select="@model"/>.form</field>
        <field name="model"><xsl:value-of select="@model"/></field>
        <field name="arch" type="xml">
            <form string="Subscription" class="o_sale_order">
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button name="toggle_active" type="object" class="oe_stat_button" icon="fa-archive">
                            <field name="active" widget="boolean_button" options="{{&quot;terminology&quot;: &quot;archive&quot;}}"/>
                        </button>
                    </div>
                    <div class="oe_title">
                        <h1>
                            <field name="name" readonly="1"/>
                        </h1>
                    </div>
                    <group>
                        <xsl:apply-templates select="field"/>
                        <field name="partner_id" domain="[('customer','=',True)]" />
                    </group>
                </sheet>
            </form>
        </field>
    </record>
  </xsl:template>
  <xsl:template match="field">
      <xsl:copy-of select="."/>
  </xsl:template>

</xsl:stylesheet> 
