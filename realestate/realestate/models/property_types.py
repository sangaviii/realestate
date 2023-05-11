from odoo import _, models, fields, api


class PropertiesTypes(models.Model):
    _name = 'property.types'

    def action_property_type(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Offers',
            'res_model': 'offer.offer',
            'domain': "[('properties_type_id', '=', active_id)]",
            'view_mode': 'tree',
            'context': "{'create': False}",
        }

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        for x in self:
            x.offer_count = len(x.offer_ids)

    name = fields.Char(string='Name')
    property_ids = fields.One2many('real.estate', 'property_type_id', string='Property')
    offer_count = fields.Integer(string='Offer Count', compute='_compute_offer_count')
    offer_ids = fields.One2many('offer.offer', 'properties_type_id', string='Offer')
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The Name must be unique !')
    ]


class RealEstate(models.Model):
    _name = 'real.estate'

    property_type_id = fields.Many2one('property.types', string='property')
    property_id = fields.Many2one('properties.properties', string='property',
                                  domain="[('property_type','=', property_type_id)]")
    status = fields.Selection(string='State', related='property_id.status')
    expected_price = fields.Float(string='Expected_price', related='property_id.expected_price')
