from django.db import models

# Create your models here.
class Tenant(models.Model):
    
    name = models.CharField(
        max_length=200,
        verbose_name="Nome della scuola",
        help_text="Es: Liceo Scientifico Einstein"
    )
    
    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="Identificatore URL",
        help_text=(
            "Versione URL-friendly del nome. Es: liceo-scientifico-einstein. "
            "Si usa negli URL per identificare la scuola in modo leggibile. "
            "Nel form admin si popola automaticamente dal campo 'name' "
            "tramite prepopulated_fields (configurato in admin.py)."
        )
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data di creazione",
        # auto_now_add=True: Django imposta questo campo automaticamente
        # alla creazione del record. Non può essere modificato manualmente.
        # Confronto con auto_now=True: quello si aggiorna ad ogni salvataggio.
    )

    class Meta:
        verbose_name = "Scuola"
        verbose_name_plural = "Scuole"
        ordering = ["name"]  # Ordine alfabetico per default in tutte le query

    def __str__(self):
        return self.name