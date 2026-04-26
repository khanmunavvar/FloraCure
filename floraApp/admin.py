from django.contrib import admin
from .models import Diagnosis, Profile


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display  = ('plant_name', 'disease', 'user', 'date', 'is_cured')
    list_filter   = ('is_cured', 'date')
    search_fields = ('plant_name', 'disease', 'user__username')
    ordering      = ('-date',)
    readonly_fields = ('date',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'get_email', 'city')
    search_fields = ('user__username', 'user__email')

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
