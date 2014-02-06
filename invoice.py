# This file is part account_invoice_shop module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['Sale', 'Invoice']
__metaclass__ = PoolMeta


class Sale:
    __name__ = 'sale.sale'

    def _get_invoice_sale(self, invoice_type):
        invoice = super(Sale, self)._get_invoice_sale(invoice_type)
        invoice.shop = self.shop
        return invoice


class Invoice:
    __name__ = 'account.invoice'

    shop = fields.Many2One('sale.shop', 'Shop',
        states={
            'required': Eval('type').in_(['out_invoice', 'out_credit_note']),
            },
        depends=['type'])

    @staticmethod
    def default_shop():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        return user.shop.id if user.shop else None

    def _credit(self):
        res = super(Invoice, self)._credit()
        res['shop'] = getattr(self, 'shop').id
        return res
