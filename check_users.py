from core.models import User

users = User.objects.all()
print(f'Total users: {users.count()}')

for user in users:
    print(f'ID: {user.id}, Email: {user.email}, Username: "{user.username}" (len={len(user.username)})')
