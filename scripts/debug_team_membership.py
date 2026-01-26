import os
import sys
import django
# Ensure project root is on sys.path so Django settings package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from core.models import User, Game
from teams.models import Team, TeamMember
from teams.views import TeamAccessMixin
from django.test.client import RequestFactory

# Create objects
u, _ = User.objects.get_or_create(username='dbg_captain', defaults={'email':'dbg@test.com'})
if not u.has_usable_password():
    u.set_password('test')
    u.save()

g, _ = Game.objects.get_or_create(name='Debug Game', slug='debug-game')
team, _ = Team.objects.get_or_create(name='Debug Team', defaults={'tag':'DBG','game':g,'captain':u,'max_members':10})
# Ensure slug set
team.save()

# Create membership
m, created = TeamMember.objects.get_or_create(team=team, user=u, defaults={'role':'captain','status':'active'})

# Build fake request
rf = RequestFactory()
req = rf.get(f'/teams/{team.slug}/settings/')
req.user = u

# Instantiate mixin class (needs minimal attrs)
class DummyView(TeamAccessMixin):
    def __init__(self, request, kwargs):
        self.request = request
        self.kwargs = kwargs

v = DummyView(req, {'slug':team.slug})
print('team pk:', team.pk)
print('membership exists:', TeamMember.objects.filter(team=team, user=u).exists())
print('members query:', list(TeamMember.objects.filter(team=team, user=u).values('id','role','status')))
try:
    mem = v.get_user_membership()
    print('get_user_membership returned:', mem)
    if mem:
        print('mem role/status:', mem.role, mem.status)
except Exception as e:
    print('error calling get_user_membership:', e)
