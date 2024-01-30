from odoo import api, fields, models, _
from datetime import datetime
from pytz import timezone as pytz
from odoo.addons.base.models.res_partner import _tz_get
from odoo.exceptions import ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    # tz_offset = fields.Char(string='TEST', readonly=False)

    # @api.depends('tz')
    # def _compute_tz_offset(self):
    #     for user in self:
    #         user.tz_offset = datetime.datetime.now(pytz.timezone(user.tz or 'GMT')).strftime('%z')