
import logging
from datetime import date
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.osv.expression import AND
import pytz


class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False, user_id=False):
        """ Serialise the orders of the requested time period, configs and sessions.

        :param date_start: The dateTime to start, default today 00:00:00.
        :type date_start: str.
        :param date_stop: The dateTime to stop, default date_start + 23:59:59.
        :type date_stop: str.
        :param config_ids: Pos Config id's to include.
        :type config_ids: list of numbers.
        :param session_ids: Pos Config id's to include.
        :type session_ids: list of numbers.

        :returns: dict -- Serialised sales.
        """
        if self.env.user.has_group('purchase.group_purchase_manager'):
            if self.env['hr.attendance'].search([('employee_id', '=', self.env.user.employee_id.id)]):
                verify_date_today = date.today().strftime('%d/%m/%Y') in self.env['hr.attendance'].search([('employee_id', '=', self.env.user.employee_id.id)])[0].display_name
            else:
                verify_date_today = False
        else:
            verify_date_today = date.today().strftime('%d/%m/%Y') in self.env['hr.attendance'].search([('employee_id', '=', self.env.user.employee_id.id)])[0].display_name

        # verify_date_today = date.today().strftime('%d/%m/%Y')  in self.env['hr.attendance'].search([('employee_id','=',self.env.user.employee_id.id)])[0].display_name
        message = ''
        if verify_date_today:
            employee_print_register = self.env['hr.attendance'].search([('employee_id','=',self.env.user.employee_id.id)])[0]
            check_in = employee_print_register.check_in if employee_print_register.check_in != False else 'No registro su hora de entrada'
            check_out = employee_print_register.check_out if employee_print_register.check_out != False else 'No registro su hora de salida'
        else:
            check_in = False
            check_out = False
        if check_in == False:
            message = 'No registro su hora de entrada en la fecha '+str(date.today())
            if check_out == False and check_in != False:
                message = 'No registro su hora de salida en la fecha '+str(date.today())

        print_register = self.env['hr.attendance'].search([('employee_id','=',self.env.user.employee_id.id)])[0].display_name if verify_date_today and check_out != False else message
        if check_out == 'No registro su hora de salida':
            print_register = print_register + ' - ' + check_out
        # print_register = print_register + ' - ' + check_out if check_out != False else message
        domain = [('state', 'in', ['paid', 'invoiced', 'done'])]
        domain_session = []
        if (session_ids and user_id != False):
            domain = AND([domain, [('session_id', 'in', session_ids)]])
        else:
            if date_start:
                date_start = fields.Date.from_string(date_start)
                # date_start = fields.Datetime.from_string(date_start)
            else:
                # start by default today 00:00:00
                user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
                today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
                date_start = today.astimezone(pytz.timezone('UTC'))

            if date_stop:
                date_stop = fields.Date.from_string(date_stop)
                # date_stop = fields.Datetime.from_string(date_stop)
                # avoid a date_stop smaller than date_start
                if (date_stop < date_start):
                    date_stop = date_start + timedelta(days=1, seconds=-1)
            else:
                # stop by default today 23:59:59
                date_stop = date_start + timedelta(days=1, seconds=-1)

            domain = AND([domain,
                          [('date_order', '>=', fields.Date.to_string(date_start)),
                           ('date_order', '<=', fields.Date.to_string(date_stop))]
                          ])
            domain_session = AND([domain_session,
                          [('start_at', '>=', fields.Date.to_string(date_start)),
                           ('start_at', '<=', fields.Date.to_string(date_stop))]
                          ])
            domain = AND([domain, [('user_id', '=', session_ids)]])

            domain_session = AND([domain_session, [('user_id.id', '=', session_ids)]])

            if config_ids:
                domain = AND([domain, [('config_id', 'in', config_ids)]])



        session_ids = self.env['pos.session'].search(domain_session)
        #orders = self.env['pos.order'].search(domain)
        total = 0.0
        payments = []
        taxes = {}
        products_sold = {}
        for session in session_ids:
            orders = session.order_ids
            user_currency = self.env.company.currency_id
            products_total_sold = []
            for order in orders:
                if user_currency != order.pricelist_id.currency_id:
                    total += order.pricelist_id.currency_id._convert(
                        order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
                else:
                    total += order.amount_total
                currency = order.session_id.currency_id

                for line in order.lines:
                    key = (line.product_id, line.price_unit, line.discount)
                    products_sold.setdefault(key, 0.0)
                    products_sold[key] += line.qty

                    if line.tax_ids_after_fiscal_position:
                        line_taxes = line.tax_ids_after_fiscal_position.sudo().compute_all(
                            line.price_unit * (1 - (line.discount or 0.0) / 100.0), currency, line.qty,
                            product=line.product_id, partner=line.order_id.partner_id or False)
                        for tax in line_taxes['taxes']:
                            taxes.setdefault(tax['id'], {'name': tax['name'], 'tax_amount': 0.0, 'base_amount': 0.0})
                            taxes[tax['id']]['tax_amount'] += tax['amount']
                            taxes[tax['id']]['base_amount'] += tax['base']
                    else:
                        taxes.setdefault(0, {'name': _('No Taxes'), 'tax_amount': 0.0, 'base_amount': 0.0})
                        taxes[0]['base_amount'] += line.price_subtotal_incl

            payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders.ids)]).ids
            if payment_ids:
                self.env.cr.execute("""
                       SELECT method.name, sum(amount) total
                       FROM pos_payment AS payment,
                            pos_payment_method AS method
                       WHERE payment.payment_method_id = method.id
                           AND payment.id IN %s
                       GROUP BY method.name
                   """, (tuple(payment_ids),))
                payments = self.env.cr.dictfetchall()
            else:
                payments = []

            products_total_sold.append(products_sold)

        return {
            'print_register': print_register,
            'user_id_name': session_ids[0].user_id.name if session_ids else 'Sin usuario',
            'currency_precision': self.env.company.currency_id.decimal_places,
            'total_paid': self.env.company.currency_id.round(total) if total else 0.0,
            'payments': payments,
            'company_name': self.env.company.name,
            'taxes': list(taxes.values()),
            'products': sorted([{
                'product_id': product.id,
                'product_name': product.name,
                'code': product.default_code,
                'quantity': qty,
                'price_unit': price_unit,
                'price_unit_original': product.list_price,
                'discount': discount,
                'uom': product.uom_id.name
            } for (product, price_unit, discount), qty in products_sold.items()], key=lambda l: l['product_name'])
        }

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        configs = self.env['pos.config'].browse(data['config_ids'])
        data.update(self.get_sale_details(data['date_start'], data['date_stop'], configs.ids, data['user_id']))
        return data