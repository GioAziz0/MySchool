from django.db import models
from django.contrib.auth.models import AbstractUser


class Permesso(models.Model):
    """
    Model for permissions in the electronic register.
    Each permission defines a specific capability.
    """
    nome = models.CharField(max_length=100, unique=True)
    descrizione = models.TextField(blank=True)

    class Meta:
        verbose_name = "Permesso"
        verbose_name_plural = "Permessi"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Ruolo(models.Model):
    """
    Model for roles (Admin, Insegnante, Studente).
    Each role has a set of default permissions.
    """
    ADMIN = 'admin'
    INSEGNANTE = 'insegnante'
    STUDENTE = 'studente'

    RUOLO_CHOICES = [
        (ADMIN, 'Admin'),
        (INSEGNANTE, 'Insegnante'),
        (STUDENTE, 'Studente'),
    ]

    nome = models.CharField(max_length=50, choices=RUOLO_CHOICES, unique=True)
    descrizione = models.TextField(blank=True)
    permessi = models.ManyToManyField(
        Permesso,
        related_name='ruoli',
        blank=True,
        verbose_name="Permessi del ruolo"
    )

    class Meta:
        verbose_name = "Ruolo"
        verbose_name_plural = "Ruoli"
        ordering = ['nome']

    def __str__(self):
        return self.get_nome_display()


class Utente(AbstractUser):
    """
    Custom User model for the electronic register.
    Extends AbstractUser with Italian-specific fields.
    """
    nome = models.CharField(max_length=100, verbose_name="Nome")
    cognome = models.CharField(max_length=100, verbose_name="Cognome")
    codice_fiscale = models.CharField(
        max_length=16,
        unique=True,
        verbose_name="Codice Fiscale",
        help_text="Codice fiscale italiano (16 caratteri)"
    )
    data_di_nascita = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data di Nascita"
    )
    ruolo = models.ForeignKey(
        Ruolo,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='utenti',
        verbose_name="Ruolo"
    )
    permessi_extra = models.ManyToManyField(
        Permesso,
        through='UtentePermesso',
        related_name='utenti',
        blank=True,
        verbose_name="Permessi Extra"
    )

    class Meta:
        verbose_name = "Utente"
        verbose_name_plural = "Utenti"
        ordering = ['cognome', 'nome']

    def __str__(self):
        return f"{self.cognome} {self.nome}"

    def get_full_name(self):
        return f"{self.nome} {self.cognome}"

    def get_all_permissions_list(self):
        """
        Returns a list of all permission names for this user.
        Includes both role-based and extra permissions.
        """
        permissions = set()
        
        # Add role permissions
        if self.ruolo:
            for perm in self.ruolo.permessi.all():
                permissions.add(perm.nome)
        
        # Add extra user-specific permissions
        for perm in self.permessi_extra.all():
            permissions.add(perm.nome)
        
        return list(permissions)

    def has_custom_permission(self, permission_name):
        """
        Check if user has a specific custom permission.
        """
        return permission_name in self.get_all_permissions_list()

    @property
    def is_admin(self):
        return self.ruolo and self.ruolo.nome == Ruolo.ADMIN

    @property
    def is_insegnante(self):
        return self.ruolo and self.ruolo.nome == Ruolo.INSEGNANTE

    @property
    def is_studente(self):
        return self.ruolo and self.ruolo.nome == Ruolo.STUDENTE


class UtentePermesso(models.Model):
    """
    Through model for extra user permissions.
    Allows assigning additional permissions beyond the role's defaults.
    """
    utente = models.ForeignKey(
        Utente,
        on_delete=models.CASCADE,
        related_name='utente_permessi'
    )
    permesso = models.ForeignKey(
        Permesso,
        on_delete=models.CASCADE,
        related_name='utente_permessi'
    )
    data_assegnazione = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = "Permesso Utente"
        verbose_name_plural = "Permessi Utente"
        unique_together = ['utente', 'permesso']
        ordering = ['utente', 'permesso']

    def __str__(self):
        return f"{self.utente} - {self.permesso}"
