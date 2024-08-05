import unittest
from decimal import Decimal

from proteus import Model, Wizard
from trytond.modules.account.tests.tools import (create_chart,
                                                 create_fiscalyear, create_tax,
                                                 get_accounts)
from trytond.modules.account_invoice.tests.tools import (
    create_payment_term, set_fiscalyear_invoice_sequences)
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.modules.sale_shop.tests.tools import create_shop
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules, set_user


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Imports

        # Install account_invoice_shop
        activate_modules('account_invoice_shop')

        # Create company
        _ = create_company()
        company = get_company()

        # Create fiscal year
        fiscalyear = set_fiscalyear_invoice_sequences(
            create_fiscalyear(company))
        fiscalyear.click('create_period')

        # Create chart of accounts
        _ = create_chart(company)
        accounts = get_accounts(company)
        revenue = accounts['revenue']
        expense = accounts['expense']
        account_cash = accounts['cash']

        # Create tax
        tax = create_tax(Decimal('.10'))
        tax.save()

        # Create payment method
        Journal = Model.get('account.journal')
        PaymentMethod = Model.get('account.invoice.payment.method')
        journal_cash, = Journal.find([('type', '=', 'cash')])
        payment_method = PaymentMethod()
        payment_method.name = 'Cash'
        payment_method.journal = journal_cash
        payment_method.credit_account = account_cash
        payment_method.debit_account = account_cash
        payment_method.save()

        # Create party
        Party = Model.get('party.party')
        party = Party(name='Party')
        party.save()
        customer = Party(name='Customer')
        customer.save()

        # Create account category
        ProductCategory = Model.get('product.category')
        account_category = ProductCategory(name="Account Category")
        account_category.accounting = True
        account_category.account_expense = expense
        account_category.account_revenue = revenue
        account_category.customer_taxes.append(tax)
        account_category.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'service'
        template.list_price = Decimal('40')
        template.account_category = account_category
        template.salable = True
        template.save()
        product, = template.products

        # Create payment term
        payment_term = create_payment_term()
        payment_term.save()

        # Create product price list
        ProductPriceList = Model.get('product.price_list')
        product_price_list = ProductPriceList()
        product_price_list.name = 'Price List'
        product_price_list.company = company
        product_price_list.save()

        # Create Sale Shop
        shop = create_shop(payment_term, product_price_list)
        shop.save()

        # Save Sale Shop User
        User = Model.get('res.user')
        user, = User.find([])
        user.shops.append(shop)
        user.shop = shop
        user.save()
        set_user(user)

        # Sale 5 products
        Sale = Model.get('sale.sale')
        SaleLine = Model.get('sale.line')
        sale = Sale()
        sale.party = customer
        sale.payment_term = payment_term
        sale.invoice_method = 'order'
        sale_line = SaleLine()
        sale.lines.append(sale_line)
        sale_line.product = product
        sale_line.quantity = 2.0
        sale_line = SaleLine()
        sale.lines.append(sale_line)
        sale_line.product = product
        sale_line.quantity = 3.0
        sale.save()
        self.assertEqual(sale.state, 'draft')
        sale.click('quote')
        sale.click('confirm')
        self.assertEqual(sale.invoice_state, 'pending')
        invoice, = sale.invoices
        self.assertEqual(invoice.shop, sale.shop)

        # Post and credit invoice
        invoice.click('post')
        self.assertEqual(invoice.state, 'posted')
        credit = Wizard('account.invoice.credit', [invoice])
        credit.execute('credit')
        credit_note, = credit.actions[0]
        self.assertEqual(credit_note.shop, sale.shop)
        self.assertEqual(credit_note.untaxed_amount, Decimal('-200.00'))

        # Test shop and invoice type
        Invoice = Model.get('account.invoice')
        invoice = Invoice()
        self.assertEqual(invoice.type, 'out')
        self.assertEqual(invoice.shop, shop)
