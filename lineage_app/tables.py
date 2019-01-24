import django_tables2 as tables
from .models import SharedDnaGenes, DiscordantSnps


class SharedDnaGenesTable(tables.Table):
    # https://stackoverflow.com/a/6275332
    details_col = tables.TemplateColumn(template_name='pages/shared_dna_genes_details_link.html',
                                        orderable=False,
                                        verbose_name='Details')

    delete_col = tables.TemplateColumn(template_name='pages/shared_dna_genes_delete_form.html',
                                       orderable=False,
                                       verbose_name='Delete')

    class Meta:
        model = SharedDnaGenes
        fields = ['individual1', 'individual2', 'cM_threshold', 'snp_threshold',
                  'total_shared_cMs_one_chrom', 'total_shared_cMs_two_chrom',
                  'total_shared_genes_one_chrom', 'total_shared_genes_two_chrom']
        template_name = 'django_tables2/bootstrap4.html'


class SharedDnaTable(tables.Table):
    segment_col = tables.Column(verbose_name='Seg')
    chrom = tables.Column(verbose_name='Chrom')
    start = tables.Column(verbose_name='Start')
    end = tables.Column(verbose_name='End')
    cMs = tables.Column(verbose_name=' cMs')
    snps = tables.Column(verbose_name='SNPs')

    class Meta:
        template_name = 'django_tables2/bootstrap4.html'

    def render_cMs(self, value):
        return '{:.2f}'.format(value)

class DiscordantSnpsTable(tables.Table):
    # https://stackoverflow.com/a/6275332
    download_col = tables.TemplateColumn(template_name='pages/discordant_snps_download_link.html',
                                        orderable=False,
                                        verbose_name='Download')

    delete_col = tables.TemplateColumn(template_name='pages/discordant_snps_delete_form.html',
                                       orderable=False,
                                       verbose_name='Delete')

    class Meta:
        model = DiscordantSnps
        fields = ['individual1', 'individual2', 'individual3', 'total_discordant_snps']
        template_name = 'django_tables2/bootstrap4.html'
