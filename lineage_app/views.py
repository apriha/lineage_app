import logging
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, Http404, JsonResponse
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse
from sendfile import sendfile
from django_tables2 import RequestConfig

from .forms import IndividualForm, SnpsForm, SharedDnaGenesForm, DiscordantSnpsForm
from .helpers import get_all_individuals_context, shared_dna_genes_calc_exists
from .models import Individual, Snps, DiscrepantSnps, SharedDnaGenes, DiscordantSnps
from .tasks import setup_snps, find_shared_dna_genes, find_discordant_snps
from .tables import SharedDnaGenesTable, SharedDnaTable, DiscordantSnpsTable

logger = logging.getLogger(__name__)


def robots(request):
    return HttpResponse("User-agent: *\nDisallow:\n", content_type="text/plain")


@login_required
def download_snps(request, uuid):
    try:
        snps = request.user.snps.get(uuid=uuid)
    except Snps.DoesNotExist:
        raise Http404

    return sendfile(request, snps.file.path, attachment=True,
                    attachment_filename=snps.get_filename())

@login_required
def download_discrepant_snps(request, uuid):
    try:
        individual = request.user.individuals.get(pk=uuid)
        discrepant_snps = individual.discrepant_snps
    except Individual.DoesNotExist:
        raise Http404
    except DiscrepantSnps.DoesNotExist:
        raise Http404

    return sendfile(request, discrepant_snps.file.path, attachment=True,
                    attachment_filename=discrepant_snps.get_filename())

@login_required
def individuals(request):
    context = get_all_individuals_context(request.user.id)
    return render(request, 'pages/individuals.html', context)


@login_required
def upload_snps(request, uuid):
    if request.method == 'POST':
        try:
            individual = request.user.individuals.get(pk=uuid)
            form = SnpsForm(request.POST, request.FILES)

            if settings.DEBUG:
                # allow progress bar to display in development
                time.sleep(0.5)

            if form.is_valid():
                snps = form.save(commit=False)
                snps.user = request.user
                snps.individual = individual
                snps.save()
                transaction.on_commit(
                    lambda: setup_snps.apply_async((snps.id,), task_id=str(snps.setup_task_id)))

                data = {'is_valid': True}
            else:
                data = {'is_valid': False}

            return JsonResponse(data)

        except Individual.DoesNotExist:
            raise Http404

    return redirect('individuals')


@login_required
def delete_snps(request, uuid):
    if request.method == 'POST':
        try:
            snps = request.user.snps.get(uuid=uuid)
            snps.delete()
        except Snps.DoesNotExist:
            raise Http404

    return redirect('individuals')


@login_required
def delete_individual(request, uuid):
    if request.method == 'POST':
        try:
            individual = request.user.individuals.get(pk=uuid)
            individual.delete()
        except Individual.DoesNotExist:
            raise Http404

    return redirect('individuals')


@login_required
def edit_individual(request, uuid):
    try:
        individual = request.user.individuals.get(pk=uuid)
    except Individual.DoesNotExist:
        raise Http404

    if request.method == 'POST':
        form = IndividualForm(request.POST, instance=individual)
        if form.is_valid():
            form.save()
            return redirect('individuals')
    else:
        form = IndividualForm(instance=individual)

    return render(request, 'pages/add_edit_individual.html',
                  {'title': 'Edit', 'form': form,
                   'action_url': reverse('edit_individual', args=[uuid])})


@login_required
def add_individual(request):
    if request.method == 'POST':
        form = IndividualForm(request.POST)
        if form.is_valid():
            individual = form.save(commit=False)
            individual.user = request.user
            individual.save()
            return redirect('individuals')
    else:
        form = IndividualForm()

    return render(request, 'pages/add_edit_individual.html',
                  {'title': 'Add', 'form': form, 'action_url': reverse('add_individual')})


@login_required
def shared_dna_genes(request):
    if request.method == 'POST':
        form = SharedDnaGenesForm(request.user, request.POST)
        if form.is_valid():
            if shared_dna_genes_calc_exists(form.cleaned_data):
                messages.add_message(request, messages.WARNING,
                                     'Requested comparison has already been calculated or is '
                                     'being calculated!')
            else:
                shared_dna_genes = form.save(commit=False)
                shared_dna_genes.user = request.user
                shared_dna_genes.save()

                transaction.on_commit(
                    lambda: find_shared_dna_genes.apply_async((shared_dna_genes.id,),
                                                              task_id=str(shared_dna_genes.setup_task_id)))

            return redirect('shared_dna_genes')
    else:
        form = SharedDnaGenesForm(request.user)

    queryset = request.user.shared_dna_genes.all().exclude(setup_complete=False).order_by('id')

    if len(queryset) > 0:
        table = SharedDnaGenesTable(queryset)
        RequestConfig(request, paginate={'per_page': 10}).configure(table)
    else:
        table = None

    return render(request, 'pages/shared_dna_genes.html',
                  {'form': form, 'table': table, 'finding_shared_dna_genes':
                      request.user.shared_dna_genes.filter(setup_complete=False).count()})


@login_required
def shared_dna_genes_details(request, uuid):
    try:
        shared_dna_genes = request.user.shared_dna_genes.get(uuid=uuid)
    except SharedDnaGenes.DoesNotExist:
        raise Http404

    if shared_dna_genes.shared_dna_one_chrom_pickle:
        shared_dna_one_chrom = shared_dna_genes.get_shared_dna_one_chrom()
        shared_dna_one_chrom_table = SharedDnaTable(shared_dna_one_chrom, prefix='1-')
        RequestConfig(request, paginate={'per_page': 5}).configure(shared_dna_one_chrom_table)
    else:
        shared_dna_one_chrom_table = None

    if shared_dna_genes.shared_dna_two_chrom_pickle:
        shared_dna_two_chrom = shared_dna_genes.get_shared_dna_two_chrom()
        shared_dna_two_chrom_table = SharedDnaTable(shared_dna_two_chrom, prefix='2-')
        RequestConfig(request, paginate={'per_page': 5}).configure(shared_dna_two_chrom_table)
    else:
        shared_dna_two_chrom_table = None

    return render(request, 'pages/shared_dna_genes_details.html',
                  {'shared_dna_genes': shared_dna_genes,
                   'shared_dna_one_chrom_table': shared_dna_one_chrom_table,
                   'shared_dna_two_chrom_table': shared_dna_two_chrom_table})


@login_required
def shared_dna_plot(request, uuid):
    try:
        shared_dna_genes = request.user.shared_dna_genes.get(uuid=uuid)
    except SharedDnaGenes.DoesNotExist:
        raise Http404

    return sendfile(request, shared_dna_genes.shared_dna_plot_png.path)


@login_required
def shared_dna_one_chrom(request, uuid):
    try:
        shared_dna_genes = request.user.shared_dna_genes.get(uuid=uuid)
    except SharedDnaGenes.DoesNotExist:
        raise Http404

    return sendfile(request, shared_dna_genes.shared_dna_one_chrom_csv.path,
                    attachment=True,
                    attachment_filename=shared_dna_genes.get_shared_dna_one_chrom_csv_filename())


@login_required
def shared_dna_two_chrom(request, uuid):
    try:
        shared_dna_genes = request.user.shared_dna_genes.get(uuid=uuid)
    except SharedDnaGenes.DoesNotExist:
        raise Http404

    return sendfile(request, shared_dna_genes.shared_dna_two_chrom_csv.path,
                    attachment=True,
                    attachment_filename=shared_dna_genes.get_shared_dna_two_chrom_csv_filename())


@login_required
def shared_genes_one_chrom(request, uuid):
    try:
        shared_dna_genes = request.user.shared_dna_genes.get(uuid=uuid)
    except SharedDnaGenes.DoesNotExist:
        raise Http404

    return sendfile(request, shared_dna_genes.shared_genes_one_chrom_csv.path,
                    attachment=True,
                    attachment_filename=shared_dna_genes.get_shared_genes_one_chrom_csv_filename())


@login_required
def shared_genes_two_chrom(request, uuid):
    try:
        shared_dna_genes = request.user.shared_dna_genes.get(uuid=uuid)
    except SharedDnaGenes.DoesNotExist:
        raise Http404

    return sendfile(request, shared_dna_genes.shared_genes_two_chrom_csv.path,
                    attachment=True,
                    attachment_filename=shared_dna_genes.get_shared_genes_two_chrom_csv_filename())


@login_required
def delete_shared_dna_genes(request, uuid):
    if request.method == 'POST':
        try:
            shared_dna_genes = request.user.shared_dna_genes.get(uuid=uuid)
            shared_dna_genes.delete()
        except Snps.DoesNotExist:
            raise Http404

    return redirect('shared_dna_genes')


@login_required
def discordant_snps(request):
    if request.method == 'POST':
        form = DiscordantSnpsForm(request.user, request.POST)
        if form.is_valid():
            discordant_snps = form.save(commit=False)
            discordant_snps.user = request.user
            discordant_snps.save()

            transaction.on_commit(
                lambda: find_discordant_snps.apply_async((discordant_snps.id,),
                                                          task_id=str(discordant_snps.setup_task_id)))

            return redirect('discordant_snps')
    else:
        form = DiscordantSnpsForm(request.user)

    queryset = request.user.discordant_snps.all().exclude(setup_complete=False).order_by('id')

    if len(queryset) > 0:
        table = DiscordantSnpsTable(queryset)
        RequestConfig(request, paginate={'per_page': 10}).configure(table)
    else:
        table = None

    return render(request, 'pages/discordant_snps.html',
                  {'form': form, 'table': table, 'finding_discordant_snps':
                      request.user.discordant_snps.filter(setup_complete=False).count()})


@login_required
def delete_discordant_snps(request, uuid):
    if request.method == 'POST':
        try:
            discordant_snps = request.user.discordant_snps.get(uuid=uuid)
            discordant_snps.delete()
        except Snps.DoesNotExist:
            raise Http404

    return redirect('discordant_snps')


@login_required
def download_discordant_snps(request, uuid):
    try:
        discordant_snps = request.user.discordant_snps.get(uuid=uuid)
    except DiscordantSnps.DoesNotExist:
        raise Http404

    return sendfile(request, discordant_snps.discordant_snps_csv.path,
                    attachment=True,
                    attachment_filename=discordant_snps.get_discordant_snps_csv_filename())

@login_required
def load_individual2_dropdown(request):
    uuid = request.GET.get('uuid')
    if uuid != '':
        # https://stackoverflow.com/a/4139956
        individuals = request.user.individuals.all().exclude(pk=uuid).order_by('pk')
    else:
        individuals = []
    return render(request, 'pages/individual_dropdown_options.html', {'individuals': individuals})


@login_required
def load_individual3_dropdown(request):
    uuid1 = request.GET.get('uuid1')
    uuid2 = request.GET.get('uuid2')
    if uuid1 != '' and uuid2 != '':
        # https://stackoverflow.com/a/25603053
        individuals = request.user.individuals.all().exclude(Q(pk=uuid1) | Q(pk=uuid2)).order_by(
            'pk')
    else:
        individuals = []
    return render(request, 'pages/individual_dropdown_options.html', {'individuals': individuals})
