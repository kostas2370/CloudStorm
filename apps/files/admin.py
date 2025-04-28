from django.contrib import admin
from .models import File, ExtractedData

# Register your models here.
admin.site.register(File)
admin.site.register(ExtractedData)
