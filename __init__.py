#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.
from trytond.pool import Pool
from .invoice import  *


def register():
    Pool.register(
        Sale,
        Invoice,
        module='account_invoice_shop', type_='model')
