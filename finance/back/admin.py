from django.contrib import admin

from back.forms import User
from back.models import Partner
from invoice.models import Payment

# Register your models here.
admin.site.register(User)
admin.site.register(Payment)
admin.site.register(Partner)
