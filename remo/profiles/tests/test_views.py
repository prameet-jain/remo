import datetime
import time

from nose.tools import eq_
from django.test.client import Client
from test_utils import TestCase

from remo.profiles.models import User


class ViewsTest(TestCase):
    fixtures = ['demo_users.json']

    def setUp(self):
        """ Setup tests """
        self.data = {'display_name': u'koki',
                     'first_name': u'first',
                     'email': u'rep@example.com',
                     'last_name': u'last',
                     'local_name': u'local',
                     'birth_date': u'1980-01-01',
                     'private_email': u'private_email@bar.com',
                     'twitter_account': u'foobar',
                     'city': u'city',
                     'region': u'region',
                     'country': u'Greece',
                     'lon': 12.23,
                     'lat': 12.23,
                     'mozillians_profile_url': u'http://mozillians.org/',
                     'jabber_id': u'foo@jabber.org',
                     'irc_name': u'ircname',
                     'linkedin_url': u'http://www.linkedin.com/',
                     'facebook_url': u'http://www.facebook.com/',
                     'diaspora_url': u'http://www.example.com/',
                     'personal_website_url': u'http://www.example.com/',
                     'personal_blog_feed': u'http://example.com/',
                     'bio': u'bio foo',
                     'mentor': 6}

    def test_invite_user(self):
        c = Client()
        c.login(username="mentor", password="passwd")
        c.post('/people/invite/', {'email': 'foobar@example.com'})

        u = User.objects.get(email="foobar@example.com")
        eq_(u.userprofile.added_by, User.objects.get(username="mentor"))

    def test_edit_profile_permissions(self):
        # user edits own profile
        c = Client()
        c.login(username="rep", password="passwd")
        response = c.get('/u/koki/edit/', follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

        # admin edits user's profile
        c = Client()
        c.login(username="admin", password="passwd")
        response = c.get('/u/koki/edit/', follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')

        # third user denied permission to edit user's profile
        c = Client()
        c.login(username="mentor", password="passwd")
        response = c.get('/u/koki/edit/', follow=True)
        self.assertTemplateUsed(response, 'main.html')

    def test_edit_profile_redirect(self):
        """
        Test that after profile redirection is correct.

        When a user edit his own profile must be redirected to
        reverse('profiles_view_my_profile') whereas when editing
        another user's profile, then user must be redirected to
        profile view of the just edited profile.
        """
        c = Client()
        c.login(username="admin", password="passwd")
        response = c.post('/u/koki/edit/', self.data, follow=True)
        eq_(response.request['PATH_INFO'], '/u/koki/')

        c = Client()
        c.login(username="rep", password="passwd")
        response = c.post('/u/koki/edit/', self.data, follow=True)
        eq_(response.request['PATH_INFO'], '/people/me/')

    def test_edit_profile(self):
        c = Client()
        c.login(username="rep", password="passwd")

        # edit with correct data
        response = c.post('/u/koki/edit/', self.data, follow=True)
        with open("/tmp/ll.html", "w") as f:
            f.write(response.content)
        eq_(response.request['PATH_INFO'], '/people/me/')

        # ensure that all user data was saved
        user = User.objects.get(username="rep")
        eq_(user.email, self.data['email'])
        eq_(user.first_name, self.data['first_name'])
        eq_(user.last_name, self.data['last_name'])

        temp_data = self.data.copy()

        # delete already checked items
        eq_(user.userprofile.mentor.id, temp_data['mentor'])
        eq_(user.userprofile.birth_date,
            datetime.date(*(time.strptime(temp_data['birth_date'],
                                          "%Y-%m-%d")[0:3])))
        for item in ['email', 'first_name', 'last_name',
                     'birth_date', 'mentor']:
            del(temp_data[item])

        # ensure that all user profile data was saved
        for field in temp_data.keys():
            eq_(getattr(user.userprofile, field), temp_data[field])

        # test with missing mandatory fields
        mandatory_fields = ['first_name', 'last_name', 'email',
                            'birth_date', 'private_email', 'city', 'region',
                            'country', 'lon', 'lat', 'mozillians_profile_url',
                            'irc_name']
        for field in mandatory_fields:
            # remove a mandatory field and ensure that edit fails
            temp_data = self.data.copy()
            del(temp_data[field])
            response = c.post('/u/koki/edit/', temp_data, follow=True)
            self.assertTemplateUsed(response, 'profiles_edit.html')

    def test_delete_profile(self):
        # user can't delete own profile
        c = Client()
        c.login(username="rep", password="passwd")
        response = c.post('/u/koki/delete/', follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

        # admin can delete user's profile
        c = Client()
        c.login(username="admin", password="passwd")
        response = c.post('/u/koki/delete/', {'delete': 'true'}, follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'success')

        # third user can't delete user's profile
        c = Client()
        c.login(username="mentor", password="passwd")
        response = c.post('/u/koki/delete/', follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'error')

    def test_profiles_me(self):
        # user gets own profile page rendered
        c = Client()
        c.login(username="rep", password="passwd")
        response = c.get('/people/me/', follow=True)
        self.assertTemplateUsed(response, 'profiles_view.html')

        # anonymous user get message to login first
        c = Client()
        response = c.get('/people/me/', follow=True)
        self.assertTemplateUsed(response, 'main.html')
        for m in response.context['messages']:
            pass
        eq_(m.tags, u'warning')

    def test_uncomplete_profile(self):
        c = Client()
        c.login(username="rep2", password="passwd")
        response = c.get('/people/me/', follow=True)
        self.assertTemplateUsed(response, 'profiles_edit.html')
