from rest_framework import serializers
from .models import Permesso, Utente

class PermessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permesso
        fields = ['id', 'nome', 'descrizione']
