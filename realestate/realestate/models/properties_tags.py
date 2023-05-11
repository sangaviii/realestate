from odoo import models, fields


class PropertiesTags(models.Model):
    _name = 'property.tags'

    name = fields.Char(string='Name')
    color = fields.Integer('Color Index', default=0)
