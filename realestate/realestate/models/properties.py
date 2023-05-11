from odoo import _, models, fields, api
from datetime import timedelta
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError


class Properties(models.Model):
    _name = 'properties.properties'
    _description = 'real estate'

    @api.model
    def _get_default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    @api.model
    def _get_default_buyer(self):
        return self.env.context.get('buyer_id', self.env.user.id)

    @api.depends('living_area', 'garden_area')
    def compute_total_area(self):
        for i in self:
            i.total_area = 0
            i.total_area = i.living_area + i.garden_area

    @api.onchange('garden')
    def onchange_garden(self):
        if self.garden:
            self.garden_area = 10
            self.orientation = 'North'
        else:
            self.garden_area = 0
            self.orientation = False

    @api.constrains('expected_price')
    def _constraint_expected_price(self):
        for i in self:
            if i.expected_price < 0:
                raise UserError('expected price must be less then ')

    def action_cancel(self):
        if self.state == 'sold':
            raise UserError('sold properties cannot be cancel ')
        else:
            self.state = 'cancel'

    def action_sold(self):
        if self.state == 'cancel':
            raise UserError('cancel properties cannot be set sold ')
        else:
            self.state = 'sold'
            self.write({
                'status': 'sold'
            })

    # Once an offer is accepted, the selling price and the  buyer should be set

    def action_bottom(self):
        for x in self:
            for em in x.offer_ids:
                em.status_stage = 'accepted'
                if em.status_stage == 'accepted':
                    self.write({
                        'selling_price': em.price,
                        'buyer_id': em.partner_id.id,
                        'status': 'offer_accepted'
                    })

    def action_refuse(self):
        for x in self:
            for em in x.offer_ids:
                em.status_stage = 'refused'
                if em.status_stage == 'refused':
                    self.write({
                        'selling_price': 0,
                        'buyer_id': ['buyer_id', '=', ''],
                        'status': 'offer_received'
                    })

    # delete a propert which is not new or sold

    def unlink(self):
        for record in self:
            if record.state not in ('New', 'Sold'):
                raise UserError("You cannot delete a property that is not in 'New' or 'Sold' state.")
        return super(self).unlink()

    @api.depends('offer_ids.price')
    def _compute_best_offer(self):
        for record in self:
            best_offer = 0.0
            for offer in record.offer_ids:
                if offer.price > best_offer:
                    best_offer = offer.price
            record.best_offer = best_offer

# selling price be lower then 90 of expected

    @api.constrains('selling_price', 'expected_price')
    def _check_selling_price(self):
        for record in self:
            if record.selling_price and record.selling_price < 0.9 * record.expected_price:
                raise ValidationError("Selling price cannot be lower than 90% of the expected price.")

    name = fields.Char(string="Name", required=True)
    property_type = fields.Many2one('property.types', string='property_type')
    post_code = fields.Integer(string='Post code')
    color = fields.Integer('Color Index', default=0)
    bedrooms = fields.Char(string='Bedroom')
    living_area = fields.Integer(string='Living area')
    expected_price = fields.Float(string='Expected price')
    best_offer = fields.Float(string='best_offer', compute='_compute_best_offer')
    selling_price = fields.Float(string='Selling price')
    availability_from = fields.Date(string='Availability Date')
    description = fields.Char(string='description')
    facades = fields.Char(string='Facades')
    garage = fields.Integer(string='Garage')
    garden = fields.Boolean(string='garden')
    garden_area = fields.Float(string='Garden area')
    total_area = fields.Integer(string='Total area', compute='compute_total_area')
    other_info = fields.Char(string='Other info')
    status = fields.Selection([('new', 'New'), ('offer_received', 'Offer_received'),
                               ('offer_accepted', 'Offer_accepted'),
                               ('sold', 'Sold')],
                              'Status', default='new')
    offer_ids = fields.One2many('offer.offer', 'property_id', string='Offer')
    user_id = fields.Many2one('res.users', string='Sale person', default=_get_default_user)
    buyer_id = fields.Many2one('res.partner', string='buyer', default=_get_default_buyer)
    tags_ids = fields.Many2many('property.tags', string="Tags")
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    orientation = fields.Selection([
        ('North', 'North'),
        ('South', 'South'),
        ('East', 'East'),
        ('West', 'West'),
    ], 'Orientation')

    state = fields.Selection([
            ('new', 'New'),
            ('sold', 'Sold'),
            ('cancel', 'Cancel'),
        ],
        string='State',
        default='new',
    )



class Offer(models.Model):
    _name = 'offer.offer'

    property_id = fields.Many2one('properties.properties', string='Property')
    price = fields.Float(string='Price')
    partner_id = fields.Many2one('res.partner')
    validity = fields.Integer(string='Validity(Days)')
    deadline = fields.Date(string='Deadline', compute='_compute_validity_date', inverse='_set_deadline')
    status_stage = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ],
        string='Status'
    )
    properties_type_id = fields.Many2one('property.types', related='property_id.property_type',
                                         string='Properties Type')

    @api.depends('validity')
    def _compute_validity_date(self):
        for offer in self:
            offer.deadline = fields.Date.today() + timedelta(days=offer.validity)

    def _set_deadline(self):
        for offer in self:
            offer.validity = (offer.deadline - fields.Date.today()).days

    @api.onchange('validity')
    def onchange_validity_days(self):
        self.deadline = fields.Date.today() + timedelta(days=self.validity)

    # click the button change a status

    def action_accept_offer(self):
        self.status_stage = 'accepted'

    def action_refuse_offer(self):
        self.status_stage = 'refused'

    @api.model
    def create(self, vals):
        # set the property state to 'Offer Received' at offer creation
        if 'property_id' in vals:
            property = self.env['properties.properties'].browse(vals['property_id'])
            property.write({'status': 'offer_received'})
        # raise an error if the user tries to create an offer with a lower amount than an existing offer
        existing_offer = self.search([('property_id', '=', vals['property_id']), ('price', '>=', vals['price'])])
        if existing_offer:
            raise exceptions.ValidationError('You cannot create an offer with a lower amount than an existing offer.')
        return super(Offer, self).create(vals)
