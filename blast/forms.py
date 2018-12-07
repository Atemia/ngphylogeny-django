from django import forms
from django.conf import settings
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

BLAST_PROGS = (
    ("blastn", "blastn"),
    ("blastp", "blastp"),
    ("blastx", "blastx"),
    ("tblastn", "tblastn"),
    ("tblastx", "tblastx"),
)

BLAST_DB = (
    ("nr", "nr"),
    ("refseq_genomic", "refseq_genomic"),
    ("refseq_rna", "refseq_rna"),
    ("refseq_protein", "refseq_protein"),
    ("swissprot", "swissprot"),
)

if settings.PASTEUR_BLAST_ACTIVATED:
    BLAST_SERVERS = (
        ("pasteur", "pasteur"),
        ("ncbi", "ncbi"),
    )
else:
    BLAST_SERVERS = (
        ("ncbi", "ncbi"),
    )

class BlastForm(forms.Form):
    sequence = forms.CharField(label='Sequence', widget=forms.Textarea)
    
    server = forms.ChoiceField(
        label='Server',
        choices=BLAST_SERVERS,
    )
    
    program = forms.ChoiceField(
        label='Program',
        choices=BLAST_PROGS,
    )
    
    database = forms.ChoiceField(
        label='Database',
        choices=BLAST_DB,
    )
    
    evalue = forms.FloatField(label='E.Value Threshold', min_value=0, max_value=1, initial=1.0E-5)
    coverage = forms.FloatField(label='Query coverage Threshold', min_value=0, max_value=1, initial=0.8)
    email = forms.CharField(label='Contact Email (optional)', required=False)

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Submit'))
        super(BlastForm, self).__init__(*args, **kwargs)
