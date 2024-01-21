from odoo import api, fields, models,_
from datetime import datetime, timedelta
class PosDetails(models.TransientModel):
    _inherit = 'pos.details.wizard'

    def default_user_default(self):
        return self.env.user.id

    user_id = fields.Many2one('res.users', string='Encargado de caja',default=default_user_default)
    start_date = fields.Date(string='Fecha de inicio', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string='Fecha final', required=True, default=fields.Date.context_today)
    flag_user = fields.Boolean(string='Activar readonly', compute='compute_flag_user', store=True)
    @api.depends('user_id')
    def compute_flag_user(self):
        if self.env.user.has_group('purchase.group_purchase_manager'):
            self.flag_user = True
        else:
            self.flag_user = False



    # @api.depends('user_id')
    # def compute_flag_user(self):
    #     if self.env.user.has_group('purchase.group_purchase_manager'):
    #         self.flag_user = True
    #     else:
    #         self.flag_user = False




    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            self.end_date = self.start_date

    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.end_date < self.start_date:
            self.start_date = self.end_date

    def generate_report(self):
        data = {'date_start': self.start_date, 'date_stop': self.end_date, 'config_ids': self.pos_config_ids.ids, 'user_id': self.user_id.id,}
        return self.env.ref('point_of_sale.sale_details_report').report_action([], data=data)



