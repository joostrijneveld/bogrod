from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError


class Account(models.Model):
    iban = models.CharField(_('iban'), max_length=34)


class Category(models.Model):
    name = models.CharField(max_length=100)


# This model is purposefully specific to ASN bank transactions, as that is
# the main use case for development of bogrod at the moment.
class Transaction(models.Model):
    booking_date = models.DateField()
    account = models.ForeignKey(Account)
    counter_account = models.ForeignKey(Account,
                                        related_name='counter_transactions')
    counter_name = models.CharField(max_length=70)
    account_currency = models.CharField(max_length=3)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    mutation_currency = models.CharField(max_length=3)
    mutation_value = models.DecimalField(max_digits=12, decimal_places=2)
    journal_date = models.DateField()
    value_date = models.DateField()

    # ASN bank uses this field to internally identify transaction types.
    # These are translated to the (potentially more generic) global code.
    internal_code = models.IntegerField()

    BOOKING_CODES = (
        ('ACC', 'Acceptgirobetaling'),
        ('AF',  'Afboeking'),
        ('AFB', 'Afbetalen'),
        ('BEA', 'Betaalautomaat'),
        ('BIJ', 'Bijboeking'),
        ('BTL', 'Buitenlandse Overboeking'),
        ('CHP', 'Chipknip'),
        ('CHQ', 'Cheque'),
        ('COR', 'Correctie'),
        ('DIV', 'Diversen'),
        ('EFF', 'Effectenboeking'),
        ('ETC', 'Euro traveller cheques'),
        ('GBK', 'GiroBetaalkaart'),
        ('GEA', 'Geldautomaat'),
        ('INC', 'Incasso'),
        ('IDB', 'iDEAL betaling'),
        ('IMB', 'iDEAL betaling via mobiel'),
        ('IOB', 'Interne Overboeking'),
        ('KAS', 'Kas post'),
        ('KTN', 'Kosten/provisies'),
        ('KST', 'Kosten/provisies'),
        ('OVB', 'Overboeking'),
        ('PRM', 'Premies'),
        ('PRV', 'Provisies'),
        ('RNT', 'Rente'),
        ('STO', 'Storno'),
        ('TEL', 'Telefonische Overboeking'),
        ('VV',  'Vreemde valuta'),
    )

    global_code = models.CharField(max_length=3, choices=BOOKING_CODES)
    sequence_number = models.IntegerField()
    reference = models.CharField(max_length=16)
    description = models.CharField(max_length=140)
    statement_number = models.IntegerField()

    class Meta:
        unique_together = ('sequence_number', 'journal_date')


class Flow(models.Model):
    transaction = models.ForeignKey(Transaction)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, blank=True, null=True)

    def clean(self):
        flow_sum = (Flow.objects.filter(transaction=self.transaction)
                                .exclude(pk=self.pk)
                                .aggregate(Sum('value')))
        if abs(flow_sum + self.value) > abs(transaction.value):
            raise ValidationError("Sum of flows cannot exceed transaction!")


class ExpectedTransaction(models.Model):
    from_date = models.DateField(blank=True, null=True)
    to_date = models.DateField(blank=True, null=True)
    from_value = models.DecimalField(max_digits=12, decimal_places=2,
                                     blank=True, null=True)
    to_value = models.DecimalField(max_digits=12, decimal_places=2,
                                   blank=True, null=True)
    account = models.ForeignKey(Account, blank=True, null=True)
    counter_account = models.ForeignKey(
        Account, blank=True, null=True,
        related_name='counter_expected_transactions'
    )
    category = models.ForeignKey(Category, blank=True, null=True)

    # This could be much more generic, but as of yet there are no use-cases.
    repeat_after_months = models.IntegerField(blank=True, null=True)

    # Initialize flow once the transaction has occurred
    flows = models.ManyToManyField(Flow, blank=True)


class Loan(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    receipt = models.ImageField()
    outgoing = models.ManyToManyField(Flow, blank=True)
    payment = models.ManyToManyField(Flow, blank=True,
                                     related_name='repaid_loans')


class InterestPeriod(models.Model):
    annual_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    from_date = models.DateField()
    to_date = models.DateField(blank=True, null=True)  # NULL signifies today
    loan = models.ForeignKey(Loan)
