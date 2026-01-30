import os
import django
import random
from datetime import date
from faker import Faker

# Configure Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MySchool.settings')
django.setup()

from django.contrib.auth import get_user_model
from usersmanager.models import Ruolo, Permesso, UtentePermesso

User = get_user_model()
fake = Faker('it_IT')

def create_permissions():
    print("Creating default permissions...")
    permissions_list = [
        ('view_register', 'Can view the electronic register'),
        ('edit_grades', 'Can edit student grades'),
        ('manage_users', 'Can manage all users and permissions'),
        ('view_homework', 'Can view homework assignments'),
        ('edit_homework', 'Can edit homework assignments'),
        ('view_demographics', 'Can view student demographic data'),
    ]
    
    perms = {}
    for nome, descrizione in permissions_list:
        perm, created = Permesso.objects.get_or_create(nome=nome, defaults={'descrizione': descrizione})
        perms[nome] = perm
        if created:
            print(f" Created permission: {nome}")
    return perms

def create_roles(perms):
    print("Creating default roles...")
    roles_config = [
        (Ruolo.ADMIN, 'Full administrative access', list(perms.values())),
        (Ruolo.INSEGNANTE, 'Teacher access', [perms['view_register'], perms['edit_grades'], perms['view_homework'], perms['edit_homework']]),
        (Ruolo.STUDENTE, 'Student access', [perms['view_homework']]),
    ]
    
    roles = {}
    for nome, descrizione, role_perms in roles_config:
        role, created = Ruolo.objects.get_or_create(nome=nome, defaults={'descrizione': descrizione})
        role.permessi.set(role_perms)
        roles[nome] = role
        if created:
            print(f" Created role: {nome}")
    return roles

def generate_codice_fiscale():
    # Very simplified CF generator logic to avoid complexity but keep it looking real
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    nums = "0123456789"
    cf = "".join(random.choices(chars, k=6)) + "".join(random.choices(nums, k=2)) + random.choice(chars) + "".join(random.choices(nums, k=2)) + random.choice(chars) + "".join(random.choices(nums, k=3)) + random.choice(chars)
    return cf

def create_fake_users(roles, count=50):
    print(f"Generating {count} fake users...")
    
    role_weights = {
        Ruolo.STUDENTE: 0.7,
        Ruolo.INSEGNANTE: 0.25,
        Ruolo.ADMIN: 0.05
    }
    
    available_roles = list(roles.values())
    weights = [role_weights.get(role.nome, 0.1) for role in available_roles]
    
    users_created = 0
    for i in range(count):
        nome = fake.first_name()
        cognome = fake.last_name()
        username = f"{nome.lower()}.{cognome.lower()}.{i}"
        email = f"{username}@example.com"
        cf = generate_codice_fiscale()
        data_nascita = fake.date_of_birth(minimum_age=10, maximum_age=70)
        
        # Try to avoid CF collisions
        while User.objects.filter(codice_fiscale=cf).exists():
            cf = generate_codice_fiscale()
            
        role = random.choices(available_roles, weights=weights, k=1)[0]
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password='Password123!',
            nome=nome,
            cognome=cognome,
            codice_fiscale=cf,
            data_di_nascita=data_nascita,
            ruolo=role
        )
        
        # Add some extra permissions to some users
        if random.random() < 0.1: # 10% chance
            possible_extra_perms = list(Permesso.objects.exclude(ruoli=role))
            if possible_extra_perms:
                extra_perm = random.choice(possible_extra_perms)
                UtentePermesso.objects.get_or_create(
                    utente=user,
                    permesso=extra_perm,
                    defaults={'note': "Experimental extra permission"}
                )
            
        users_created += 1
        if i % 10 == 0:
            print(f" Created {i} users...")

    print(f"Successfully created {users_created} users.")

if __name__ == '__main__':
    print("--- Starting database population ---")
    perms = create_permissions()
    roles = create_roles(perms)
    create_fake_users(roles, 50)
    print("--- Database population complete ---")
