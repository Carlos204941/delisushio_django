from django.contrib import admin
from .models import BusinessHours


@admin.register(BusinessHours)
class BusinessHoursAdmin(admin.ModelAdmin):
    list_display = ['get_day_of_week_display', 'is_open', 'opening_time', 'closing_time']
    list_editable = ['is_open', 'opening_time', 'closing_time']
    ordering = ['day_of_week']

    @admin.display(description='Day')
    def get_day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
