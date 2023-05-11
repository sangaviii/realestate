from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class Properties(models.Model):
    _inherit = 'properties.properties'

    invoice = fields.Many2one('account.move', string='Invoice', readonly=True, copy=True)

    def action_sold(self):
        res = super(Properties, self).action_sold()
        _logger.info('Property %s has been sold', self.name)

        # Create an empty account.move (customer invoice)
        invoice = self.env['account.move'].create({
            'partner_id': self.buyer_id.id,
            'move_type': 'out_invoice',
        })
        # Add two invoice lines to the invoice
        invoice_lines = []
        administrative_fees = 100.00
        invoice_lines.append((0, 0, {
            'name': self.name,
            'price_unit': self.selling_price * 0.06,
        }))
        invoice_lines.append((0, 0, {
            'name': 'Administrative fees',
            'price_unit': administrative_fees,
        }))
        invoice.write({'invoice_line_ids': invoice_lines})

        return res

