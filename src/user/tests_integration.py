import json

from django.test import TestCase

from django.contrib.auth import get_user_model

class UserTest(TestCase):

    def _user_registration(self, credentials: dict[str, str]):
        response = self.client.post('/user/registration/', credentials)
        return response
        
    def _login_by_username(self, credentials: dict[str, str]):
        response = self.client.post('/user/login/', {'username': credentials['username'], 'password': credentials['password1']})
        return response
    
    def _login_by_email(self, credentials: dict[str, str]):
        response = self.client.post('/user/login/', {'username': credentials['email'], 'password': credentials['password1']})
        return response

    def _logout(self):
        response = self.client.get('/user/logout/')
        return response
    
    def _user_profile(self, credentials: dict[str, str]):
        response = self.client.post('/user/profile/', data=credentials)
        return response

    def _check_authentication_status(self) -> bool:
        response = self.client.get('/user/check-status/')
        return json.loads(response.content)['status']
    
    def _clear_database(self):
        get_user_model().objects.first().delete()

    def test_user(self):
        credentials = {
            'username': 'test_user',
            'email': 'user123@example.com',
            'password1': 'test_password',
            'password2': 'test_password'
            }
        
        credentials_for_update = {
            'username': 'test_user_updated',
            'email': 'user1234@example.com',      
        }
        
        registration_response = self._user_registration(credentials=credentials)
        self.assertEqual(registration_response.status_code, 302)
        self.assertEqual(get_user_model().objects.all().exists(), True)

        login_by_username_response = self._login_by_username(credentials=credentials)
        self.assertEqual(login_by_username_response.status_code, 302)
        self.assertEqual(self._check_authentication_status(), True)

        logout_response = self._logout()
        self.assertEqual(logout_response.status_code, 302)
        self.assertEqual(self._check_authentication_status(), False)

        login_by_email_response = self._login_by_email(credentials=credentials)
        self.assertEqual(login_by_email_response.status_code, 302)
        self.assertEqual(self._check_authentication_status(), True)

        profile_response = self._user_profile(credentials_for_update)
        self.assertEqual(profile_response.status_code, 302)
        self.assertEqual(get_user_model().objects.first().username, credentials_for_update['username'])        

        self._clear_database()

