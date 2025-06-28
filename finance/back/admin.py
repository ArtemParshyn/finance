from django.contrib import admin
from back.forms import User
from invoice.models import Payment
from partners.models import Partner

# Register your models here.
admin.site.register(User)
admin.site.register(Payment)
admin.site.register(Partner)
