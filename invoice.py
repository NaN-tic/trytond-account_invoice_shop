# This file is part account_invoice_shop module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond import backend
from trytond.model import fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval


class Sale(metaclass=PoolMeta):
    __name__ = 'sale.sale'

    def _get_invoice_sale(self):
        invoice = super(Sale, self)._get_invoice_sale()
        invoice.shop = self.shop
        return invoice


class Invoice(metaclass=PoolMeta):
    __name__ = 'account.invoice'

    shop = fields.Many2One('sale.shop', 'Shop', domain=[
            ('company', '=', Eval('company')),
        ],
        states={
            'readonly': ((Eval('state') != 'draft')
                | (Eval('lines', [0]) & Eval('currency'))),
            })

    @classmethod
    def __register__(cls, module_name):
        super(Invoice, cls).__register__(module_name)
        table = backend.TableHandler(cls, module_name)
        table.not_null_action('shop', 'remove')

    @classmethod
    def __setup__(cls):
        super(Invoice, cls).__setup__()
        cls.currency.states['readonly'] |= Eval('shop')
        cls.currency.depends.add('shop')

    @fields.depends('shop')
    def on_change_shop(self):
        if self.shop and self.shop.currency:
            self.currency = self.shop.currency

    @fields.depends(methods=['set_shop'])
    def on_change_type(self):
        super().on_change_type()
        self.set_shop()

    @fields.depends('type', 'shop')
    def set_shop(self):
        User = Pool().get('res.user')

        if self.type == 'out':
            user = User(Transaction().user)
            if not self.shop:
                self.shop = user.shop

    def _credit(self, **values):
        credit = super(Invoice, self)._credit(**values)
        credit.shop = self.shop
        return credit
