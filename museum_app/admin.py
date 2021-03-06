from django.contrib import admin
from .models import *
from datetime import date, timedelta
from django.db.models import Sum


@admin.register(Artwork)
class ArtworkAd(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'period',
        'room',
        'creation_date',
        'entry_date',
        'economic_valuation',
        current_state,
    )
    search_fields = [
        'name',
        'author',
        'period',
    ]
    list_filter = (
        'author',
        'period',
    )


@admin.register(Painting)
class PaintingAd(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'period',
        'room',
        'creation_date',
        'entry_date',
        'economic_valuation',
        'technique',
        'style',
        current_state,
    )
    search_fields = [
        'name',
        'technique',
        'style',
    ]
    list_filter = (
        'technique',
        'style',
    )


@admin.register(Sculpture)
class SculptureAd(admin.ModelAdmin):
    list_display = (
        'name',
        'author',
        'period',
        'room',
        'creation_date',
        'entry_date',
        'economic_valuation',
        'material',
        'style',
        current_state,
    )
    search_fields = [
        'name',
        'material',
        'style',
    ]
    list_filter = (
        'material',
        'style',
        )


@admin.register(CollaboratingMuseum)
class CollaboratingMuseumAd(admin.ModelAdmin):
    list_display = (
        'name',
    )
    search_fields = [
        'name',
    ]


@admin.register(Loan)
class LoanAd(admin.ModelAdmin):
    list_display = (
        'artwork',
        'collaborating_museum',
        'loan_time',
        'date_time',
        'amount_received',
        'loan_init',
    )
    search_fields = [
        'artwork',
        'collaborating_museum',
    ]
    list_filter = (
        'artwork',
        'collaborating_museum',
    )


@admin.register(Restoration)
class RestorationAd(admin.ModelAdmin):
    list_display = (
        'artwork',
        'restoration_type',
        'date_time',
        'finish_date',
    )
    search_fields = [
        'artwork',
        'restoration_type',
    ]
    list_filter = (
        'artwork',
        'restoration_type',
    )


@admin.register(Exhibition)
class ExhibitionAd(admin.ModelAdmin):
    list_display = (
        'artwork',
        'date_time',
    )
    search_fields = [
        'artwork',
    ]


@admin.register(Room)
class RoomAd(admin.ModelAdmin):
    list_display = (
        'name',
    )
    search_fields = [
        'name',
    ]


@admin.action(description='Finish Restoration')
def finish_restoration(modeladmin, request, queryset):
    for a in queryset:
        a.finish_date = date.today()
        a.save()
        new = Exhibition(artwork=a.artwork, date_time=datetime.today())
        new.save()

@admin.register(CurrentRestoration)
class CurrentRestorationAd(admin.ModelAdmin):
    list_display = (
        'artwork',
        'restoration_type',
        'date_time',
        'finish_date',
    )
    actions = [finish_restoration]

    def get_queryset(self, request):
        states =[]
        for art in  Artwork.objects.all():
            if str(current_state(art)) == 'Restoration' and current_state(art).finish_date == None:
                states.append(current_state(art).id)
        qs = super().get_queryset(request).filter(pk__in=states)
        return qs


@admin.register(ManagerArtworks)
class ManagerArtworksAd(admin.ModelAdmin):
    change_list_template = 'admin/economic_evaluation.html'

    
    def changelist_view(self, request):
        response = super().changelist_view(
            request,
        )

        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response

        metrics = {
            'total': Sum('economic_valuation'),
        }

        response.context_data['summary'] = list(
            qs
            .order_by('-economic_valuation')
        )
        response.context_data['summary_total'] = dict(
            qs.aggregate(**metrics)
        )
        return response


@admin.display(description='Finish Date of Last Restoration',)
def last_restoration(obj: Artwork):
    return Restoration.objects.all().filter(artwork__id=obj.id).order_by('-finish_date').first().finish_date


@admin.action(description='Send to Restoration')
def send_to_restoration(modeladmin, request, queryset):
    for a in queryset:
        new = Restoration(artwork=a, date_time=datetime.today())
        new.save()

@admin.register(ToRestoration)
class ToRestorationAd(admin.ModelAdmin):
    list_display = (
        'name',
        'room',
        last_restoration,
    )
    actions = [send_to_restoration]

    def get_queryset(self, request):
        restoration_state= []
        exhibition_state= []
        to_restoration=[]

        for a in Artwork.objects.all():
            currently_restoration = False
            states = Restoration.objects.filter(artwork__id=a.id).order_by('-date_time')

            for b in states:
                if b.finish_date == None:
                    currently_restoration = True

            if not currently_restoration:
                if len(states) > 0:
                    restoration_state.append(states[0])
                else:
                    exhibition_state.append(a)

        for a in exhibition_state:
            states = Exhibition.objects.filter(artwork__id=a.id).order_by('date_time')
            if len(states) > 0:
                restoration_state.append(states[0])

        for a in restoration_state:
            if str(a) == 'Restoration':
                if a.finish_date != None and a.finish_date + timedelta(days=1825) <= date.today():
                    to_restoration.append(a.artwork.id)
            else:
                if a.date_time != None and a.date_time.date() + timedelta(days=1825) <= date.today():
                    to_restoration.append(a.artwork.id)

        return Artwork.objects.all().filter(id__in=to_restoration)


@admin.display(description='Current State',)
def current_state_loan(obj: Loan):
    if obj.loan_init == None:
        return 'On Waiting List'
    return 'currently on Loan'

@admin.register(LoanWaitList)
class LoanWaitListAd(admin.ModelAdmin):
    list_display = (
        'artwork',
        'date_time',
        'collaborating_museum',
        'loan_time',
        'loan_init',
        current_state_loan,
    )

    search_fields = [
        'artwork',
    ]

    list_filter = (
        'artwork',
    )

    def get_queryset(self, request):
        qs1= Loan.objects.all().filter(loan_init=None)
        qs2= Loan.objects.all().exclude(loan_init=None)
        qs=[]

        for a in qs2:
            if a.loan_init + timedelta(days=a.loan_time) > date.today():
                qs.append(a.id)

        for a in qs1:
            qs.append(a.id)

        qs = Loan.objects.all().filter(id__in=qs).order_by('artwork')

        for a in Artwork.objects.all():
            g1= qs1.filter(artwork__id=a.id).order_by('-loan_init')
            g2= qs.filter(artwork__id=a.id).exclude(loan_init=None)

            if len(g1) > 0 and len(g2) == 0:
                g3= qs2.filter(artwork__id=a.id).order_by('-loan_init').first()
                g=g1.first()
                g.loan_init= g3.loan_init + timedelta(days=g3.loan_time)
                g.save()
            if len(g1) == 0 and len(g2) == 0 and str(current_state(a)) == 'Loan':
                new = Exhibition(artwork=a, date_time=datetime.today())
                new.save()
                
        return qs.order_by('date_time')