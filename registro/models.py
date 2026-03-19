from django.db import models
from django.contrib.auth.models import User, AbstractUser, Permission
from django.core.validators import MinLengthValidator
import re

cf_regex = r"^[A-Z]{6}[0-9LMNPQRSTUV]{2}[ABCDEHLMPRST]{1}[0-9LMNPQRSTUV]{2}[A-Z]{1}[0-9LMNPQRSTUV]{3}[A-Z]{1}$"

# Create your models here.
class Utente(AbstractUser):

    nome = models.CharField(max_lenght=100, 
                            verbose_name="Nome")
    cognome = models.CharField(max_lenght=100, 
                               verbose_name="Cognome")
    codice_fiscale = models.CharField(
        max_length=16,
        unique=True,
        verbose_name="Codice Fiscale",
        help_text="Codice fiscale (16 caratteri)",
        validators= [
            MinLengthValidator(16),
        ]
    )
    data_nascita = models.DateField(
        inizio = models.DateField(
        verbose_name=""
    )
    fine = models.DateField(
        verbose_name=""
    )
    )

class AnnoScolastico(models.Model):
    inizio = models.DateField()

class Classe(models.Model):
    nome = models.CharField(
        max_length=10,
    )
    anno_scolastico = models.OneToOneField(AnnoScolastico, on_delete=models.CASCADE)

class periodoScolasticoStudente(models.Model):
    studente = models.OneToOneField(User, on_delete=models.CASCADE)
    anno_scolastico = models.OneToOneField(AnnoScolastico, on_delete=models.CASCADE)
    inizio = models.DateField(
        verbose_name=""
    )
    fine = models.DateField(
        verbose_name=""
    )

class Materia(models.Model):
    ...
class Voto(models.Model):
    insegnante = models.OneToOneField(User, on_delete=models.CASCADE)
    voto = models.IntegerField()
    materia = ...
    descrizione = models.CharField(max_length=100)
    ...

class EventoAppello(models.Model):
    responsabile = ... # Insegnante o Admin che segnala l'evento
    ...
    class Meta:
        permissions = [
            ('Giustifica', 'permette di giustificare un evento-appello')
        ]

class Note(models.Model):
    ...

class Studente(models.Model):
    studente = models.OneToOneField(User, on_delete=models.CASCADE)
    padre = models.OneToOneField(User, 
                                 on_delete=models.CASCADE,
                                 null=True)
    madre = models.OneToOneField(User, 
                                 on_delete=models.CASCADE,
                                 null=True)
    tutore = models.OneToOneField(User, 
                                 on_delete=models.CASCADE,
                                 null=True)
    