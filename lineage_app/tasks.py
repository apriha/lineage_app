import logging

from celery import shared_task
from celery_progress.backend import ProgressRecorder

from .models import Snps, SharedDnaGenes, DiscordantSnps

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def setup_snps(self, snps_id):
    progress_recorder = ProgressRecorder(self)
    snps = Snps.objects.get(id=snps_id)
    snps.setup(progress_recorder=progress_recorder)


@shared_task(bind=True)
def find_shared_dna_genes(self, shared_dna_genes_id):
    progress_recorder = ProgressRecorder(self)
    shared_dna_genes = SharedDnaGenes.objects.get(id=shared_dna_genes_id)
    shared_dna_genes.find_shared_dna_genes(progress_recorder=progress_recorder)


@shared_task(bind=True)
def find_discordant_snps(self, discordant_snps_id):
    progress_recorder = ProgressRecorder(self)
    discordant_snps = DiscordantSnps.objects.get(id=discordant_snps_id)
    discordant_snps.find_discordant_snps(progress_recorder=progress_recorder)
