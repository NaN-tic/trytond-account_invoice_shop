# This file is part account_invoice_shop module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['Invoice']
__metaclass__ = PoolMeta


class Invoice:
    __name__ = 'account.invoice'

    shop = fields.Many2One('sale.shop', 'Shop',
        states={'required': Eval('state') != 'draft'},
        select=True, depends=['state'])

    @classmethod
    def __setup__(cls):
        super(Invoice, cls).__setup__()
        cls._error_messages.update({
                'not_invoice_shop': 'What shop would like to sell? '
                    'Go to preferences',
                'invoice_not_shop': 'Invoice have not related a shop',
                'edit_invoice_by_shop': 'You cannot edit this invoice '
                    'because you do not have permission to edit in this shop.',
        })

    @staticmethod
    def default_shop():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        return user.shop.id if user.shop else None

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            User = Pool().get('res.user')
            user = User(Transaction().user)

            if not user.id == 0 and not user.shop:
                cls.raise_user_error('not_sale_shop')

            vals = vals.copy()
            if not 'shop' in vals:
                vals['shop'] = user.shop.id
        return super(Invoice, cls).create(vlist)

    @classmethod
    def write(cls, invoices, vals):
        '''
        Only edit Invoice users available edit in this shop
        '''
        User = Pool().get('res.user')
        user = User(Transaction().user)

        if not user.id == 0:
            shops = [s.id for s in user.shops]
            for invoice in invoices:
                if not invoice.shop:
                    cls.raise_user_error('invoice_not_shop')
                if not invoice.shop.id in shops:
                    cls.raise_user_error('edit_invoice_by_shop')
        super(Invoice, cls).write(invoices, vals)
