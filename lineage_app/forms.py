from django import forms
from django.db.models import Q

from .models import Individual, Snps, SharedDnaGenes, DiscordantSnps


class IndividualForm(forms.ModelForm):
    class Meta:
        model = Individual
        fields = ["name"]


class SnpsForm(forms.ModelForm):
    class Meta:
        model = Snps
        fields = ["file"]


class SharedDnaGenesForm(forms.ModelForm):
    class Meta:
        model = SharedDnaGenes
        fields = ["individual1", "individual2", "cM_threshold", "snp_threshold"]

    # https://stackoverflow.com/a/51939392
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["individual1"].queryset = user.individuals.all().order_by(
            "created_at"
        )
        self.fields["individual2"].queryset = Individual.objects.none()

        if "individual1" in self.data:
            try:
                self.fields["individual2"].queryset = (
                    user.individuals.all()
                    .exclude(pk=self.data.get("individual1"))
                    .order_by("created_at")
                )
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset


class DiscordantSnpsForm(forms.ModelForm):
    class Meta:
        model = DiscordantSnps
        fields = ["individual1", "individual2", "individual3"]

    # https://stackoverflow.com/a/51939392
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["individual1"].queryset = user.individuals.all().order_by(
            "created_at"
        )
        self.fields["individual2"].queryset = Individual.objects.none()
        self.fields["individual3"].queryset = Individual.objects.none()

        if "individual1" in self.data:
            try:
                self.fields["individual2"].queryset = (
                    user.individuals.all()
                    .exclude(pk=self.data.get("individual1"))
                    .order_by("created_at")
                )
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset

        if "individual2" in self.data:
            try:
                self.fields["individual3"].queryset = (
                    user.individuals.all()
                    .exclude(
                        Q(pk=self.data.get("individual1"))
                        | Q(pk=self.data.get("individual2"))
                    )
                    .order_by("created_at")
                )
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
