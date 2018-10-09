# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from Bio.Phylo.TreeConstruction import DistanceTreeConstructor, DistanceMatrix
from Bio import Phylo

from datetime import datetime
import uuid
import textwrap
import logging
import StringIO

from .trees import prot_dist, nucl_dist


class BlastRun(models.Model):
    PENDING = 'P'
    RUNNING = 'R'
    FINISHED = 'F'
    ERROR = 'E'
    RUNSTATUS = (
        (PENDING, 'Pending'),
        (RUNNING, 'Running'),
        (FINISHED, 'Finished'),
        (ERROR, 'Error')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.CharField(null=True, max_length=100)
    date = models.DateTimeField(default=datetime.now, blank=True)
    query_id = models.CharField(null=True, max_length=1000)
    query_seq = models.TextField(null=True)
    evalue = models.FloatField(default=0.00001)
    coverage = models.FloatField(default=0.8)
    database = models.CharField(max_length=100, default='swissprot')
    blastprog = models.CharField(max_length=100, default='blastp')
    status = models.CharField(max_length=1, default=PENDING, choices=RUNSTATUS)
    message = models.TextField(null=True)
    deleted = models.BooleanField(default=False)
    tree = models.TextField(null=True)

    def format_sequence(self):
        return ('\n'.join(textwrap.wrap(self.query_seq, 60))).rstrip()

    def to_fasta(self):
        fasta = ">%s\n" % self.query_id
        fasta += "%s\n" % self.format_sequence()
        for s in self.blastsubject_set.all():
            fasta += ">%s\n" % s.subject_id
            fasta += "%s\n" % s.format_sequence()
        return fasta

    def status_str(self):
        for (code, desc) in self.RUNSTATUS:
            if self.status == code:
                return desc
        return 'Error'

    def finished(self):
        '''
        Nor running anymore (success or error)
        '''
        return self.status == self.FINISHED or self.status == self.ERROR

    def soft_delete(self):
        self.deleted = True
        self.blastsubject_set.all().delete()
        self.save()

    def is_prot(self):
        return self.blastprog in ['blastp', 'blastx', 'tblastn', 'tblastx']

    def build_nj_tree(self):
        dm = self.distance_matrix()
        constructor = DistanceTreeConstructor()
        tree = constructor.nj(dm)
        treeio = StringIO.StringIO()
        Phylo.write(tree, treeio, 'newick')
        treestr = treeio.getvalue()
        treeio.close()
        return treestr

    def distance_matrix(self):
        names = []
        matrix = []
        seqs = []
        names.append(str(self.query_id))
        seqs.append("".join(self.query_seq))
        for s in self.blastsubject_set.all():
            id = s.subject_id
            seq = s.subject_seq
            names.append(str(id))
            seqs.append("".join(seq))
        for i in range(0, len(names)):
            matrix.append([])
            for j in range(0, i+1):
                d = 0.0
                if i != j:
                    if self.is_prot():
                        d = prot_dist(seqs[i], seqs[j])
                    else:
                        d = nucl_dist(seqs[i], seqs[j])
                matrix[i].append(d)
        return DistanceMatrix(names=names, matrix=matrix)


class BlastSubject(models.Model):
    subject_id = models.CharField(max_length=1000)
    subject_seq = models.TextField()
    blastrun = models.ForeignKey(BlastRun, on_delete=models.CASCADE)

    def format_sequence(self):
        unalignseq = self.subject_seq.replace("-", "")
        return ('\n'.join(textwrap.wrap(unalignseq, 60))).rstrip()