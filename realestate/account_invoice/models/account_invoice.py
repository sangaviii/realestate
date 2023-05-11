from odoo import models, fields


class Invoice(models.Model):
    _inherit = 'account.move'

    property_id = fields.Many2one('properties.properties', string='Property')

