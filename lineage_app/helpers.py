import logging
import os
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.db.models import Q
import ohapi

from .models import Individual, parse_snps

logger = logging.getLogger(__name__)

User = get_user_model()


def get_all_individuals_context(user_id):
    user = User.objects.get(id=user_id)
    individuals = []
    for individual in user.individuals.all().order_by('created_at'):
        individuals.append(get_individual_context(individual.pk))
    return {'individuals': individuals}


def get_individual_context(individual_id):
    individual = Individual.objects.get(pk=individual_id)
    return {'obj': individual, 'snps': individual.snps.all().order_by('id')}


def get_individual_snps(individual_id):
    individual = Individual.objects.get(pk=individual_id)
    return individual.snps.all().order_by('source').values('id', 'source')


def setup_oh_individual(individual_id, progress_recorder):
    individual = Individual.objects.get(pk=individual_id)
    user = individual.user

    # download, load, and analyze user data
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            progress_recorder.set_progress(1, 6)  # download data

            ohapi.command_line.download(directory=tmpdir,
                                        access_token=user.openhumansmember.get_access_token())


            progress_recorder.set_progress(2, 6)  # analyze files

            files = get_paths_to_downloaded_data_files(tmpdir)

            for file in files:
                summary_info, is_valid = parse_snps(file)

                if not is_valid:
                    continue

                individual.add_snps(file, summary_info)

        except Exception as err:
            logger.error(err)

    progress_recorder.set_progress(3, 6)  # merge SNPs
    individual.merge_snps()

    progress_recorder.set_progress(4, 6)  # remap SNPs
    individual.remap_snps()

    progress_recorder.set_progress(5, 6)  # upload files
    upload_files(individual)

    progress_recorder.set_progress(6, 6)  # complete!
    user.setup_complete = True
    user.save()


def clean_ancestry_files(ancestry_files):
    for file in ancestry_files:
        temp = os.path.join(os.path.dirname(file), 'temp.txt')
        with open(file, 'r') as f_in, open(temp, 'w') as f_out:
            lines = f_in.readlines()
            count = 0

            for line in lines:
                count += 1
                if 'rsid' in line:
                    if 'allele2r' in line:
                        line1, line2 = line.split('allele2')
                        line1 += 'allele2\n'
                        f_out.write(line1)
                        f_out.write(line2)
                    else:
                        f_out.write(line)
                    break
                else:
                    f_out.write(line)

            f_out.writelines(lines[count:])

        shutil.move(temp, file)


def get_paths_to_downloaded_data_files(path):
    listing = os.walk(path)

    data_files = []
    ancestry_files = []
    for item in listing:
        if len(item[2]) > 0:  # if one or more files
            for file in item[2]:
                file_path = os.path.join(item[0], file)
                if '.txt' in file or '.csv' in file:
                    data_files.append(file_path)  # found a raw data file

                if 'Ancestry' in file and '.txt' in file:
                    ancestry_files.append(file_path)

    # add new-line character to early OH ancestry files
    clean_ancestry_files(ancestry_files)

    return data_files


def upload_files(individual):
    files_to_upload = []

    with tempfile.TemporaryDirectory() as tmpdir:
        snps = individual.snps.filter(Q(generated_by_lineage=True) & Q(build=37))

        lineage_GRCh37 = os.path.join(tmpdir, 'lineage_GRCh37.csv')
        shutil.copy(snps[0].file.path, lineage_GRCh37)

        files_to_upload.append({'file': lineage_GRCh37, 'tags': ['snps', 'genotype', 'GRCh37',
                                                                 'Build 37', 'lineage'],
                            'description': 'SNPs merged (if applicable) and mapped relative to '
                                           'the GRCh37 assembly'})

        snps = individual.snps.filter(Q(generated_by_lineage=True) & Q(build=36))

        lineage_NCBI36 = os.path.join(tmpdir, 'lineage_NCBI36.csv')
        shutil.copy(snps[0].file.path, lineage_NCBI36)

        files_to_upload.append({'file': lineage_NCBI36, 'tags': ['snps', 'genotype', 'NCBI36',
                                                                 'Build 36', 'lineage'],
                            'description': 'SNPs merged (if applicable) and mapped relative to '
                                           'the NCBI36 assembly'})

        snps = individual.snps.filter(Q(generated_by_lineage=True) & Q(build=38))

        lineage_GRCh38 = os.path.join(tmpdir, 'lineage_GRCh38.csv')
        shutil.copy(snps[0].file.path, lineage_GRCh38)

        files_to_upload.append({'file': lineage_GRCh38, 'tags': ['snps', 'genotype', 'GRCh38',
                                                                 'Build 38', 'lineage'],
                            'description': 'SNPs merged (if applicable) and mapped relative to '
                                           'the GRCh38 assembly'})

        discrepant_snps = individual.get_discrepant_snps()
        if discrepant_snps:
            discrepant_snps_file = os.path.join(tmpdir, 'lineage_discrepant_snps.csv')
            shutil.copy(discrepant_snps.file.path, discrepant_snps_file)

            files_to_upload.append({'file': discrepant_snps_file, 'tags': ['snps', 'lineage'],
                            'description': 'Discrepant SNPs found while merging files'})


        for file in files_to_upload:
            upload_file_oh(file['file'], individual.user.id, file['tags'], file['description'])


def upload_file_oh(path, user_id, tags, description):
    """ Uploads a file to Open Humans.

    Parameters
    ----------
    path : str
        path to file
    user_id
    tags : list
        list of str tags
    description

    """
    user = User.objects.get(id=user_id)

    ohapi.api.upload_file(target_filepath=path,
                          metadata={'tags': tags, 'description': description},
                          access_token=user.openhumansmember.get_access_token())


def shared_dna_genes_calc_exists(d):
    if d['individual1'].shared_dna_genes_ind1.filter(Q(individual2=d['individual2']) &
                                                     Q(cM_threshold=d['cM_threshold']) &
                                                     Q(snp_threshold=d['snp_threshold'])):
        return True
    elif d['individual2'].shared_dna_genes_ind1.filter(Q(individual2=d['individual1']) &
                                                       Q(cM_threshold=d['cM_threshold']) &
                                                       Q(snp_threshold=d['snp_threshold'])):
        return True

    return False
