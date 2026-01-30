from rest_framework import generics, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Permesso, Utente
from .serializers import PermessoSerializer

class MyPermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        perms = user.get_all_permissions_list()
        return Response({'permissions': perms})

# class PermessoViewSet(viewsets.ModelViewSet):
#     queryset = Permesso.objects.all()
#     serializer_class = PermessoSerializer
#     permission_classes = [permissions.IsAdminUser]

class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        print(request.user.ruolo)
        if request.user:
            print("user ok")
        if request.user.is_authenticated:
            print("authenticated ok")
        if request.user.ruolo == 'Admin':
            print("admin ok")
        return request.user and request.user.is_authenticated and str(request.user.ruolo) == 'Admin'

class UserPermissionsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request, username):
        user = Utente.objects.get(username=username)
        perms = user.get_all_permissions_list()
        user.save()
        return Response({'permissions': perms})

    def post(self, request, username):
        user = Utente.objects.get(username=username)
        perm_name = request.data.get('perm_name')
        if not perm_name:
             return Response({'error': 'perm_name is required'}, status=400)
        try:
            perm = Permesso.objects.get(nome=perm_name)
        except Permesso.DoesNotExist:
             return Response({'error': 'Permission not found'}, status=404)
        user.permessi_extra.add(perm)
        user.save()
        return Response({'permissions': user.get_all_permissions_list()})

class ManagePermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, username, perm_name):
        user = Utente.objects.get(username=username)
        perm = Permesso.objects.get(nome=perm_name)
        user.permessi_extra.remove(perm)
        new_perm_name = request.data.get('perm_name')
        if not new_perm_name:
             return Response({'error': 'perm_name is required'}, status=400)
        
        try:
             perm = Permesso.objects.get(nome=new_perm_name)
        except Permesso.DoesNotExist:
             return Response({'error': 'Permission not found'}, status=404)

        user.permessi_extra.add(perm)
        perms = user.get_all_permissions_list()
        user.save()
        return Response({'permissions': perms})

    def delete(self, request, username, perm_name):
        user = Utente.objects.get(username=username)
        perm = Permesso.objects.get(nome=perm_name)
        user.permessi_extra.remove(perm)
        perms = user.get_all_permissions_list()
        user.save()
        return Response({'permissions': perms})