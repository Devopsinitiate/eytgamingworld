import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()

from django.test import Client
from core.models import User, Game
from teams.models import Team, TeamMember

# Create data
u = User.objects.create_user(username='dbgcap', email='dbgcap@test.com', password='testpass')
g = Game.objects.create(name='DBG', slug='dbg')
team = Team.objects.create(name='DBG Team', tag='DBG', game=g, captain=u, max_members=10)
TeamMember.objects.create(team=team, user=u, role='captain', status='active')

c = Client()
logged = c.login(username='dbgcap', password='testpass')
print('logged in:', logged)
resp = c.get(f'/teams/{team.slug}/settings/', follow=True)
print('final status code:', resp.status_code)
print('redirect chain:', resp.redirect_chain)
print('content snippet:', resp.content[:1000])
# print messages
for m in resp.context.get('messages', []):
    print('message:', m.level, m.message)
