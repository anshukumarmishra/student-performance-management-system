from unittest.mock import patch
from urllib.parse import urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase


class WelcomeEmailSignalTests(TestCase):
    @patch('core.signals.Thread')
    @patch('core.signals.send_mail')
    def test_new_email_account_queues_password_setup_email(
        self,
        send_mail,
        thread_class,
    ):
        user = get_user_model().objects.create_user(
            username='newstudent',
            email='student@example.com',
            password='temporary-password',
        )

        thread_class.assert_called_once()
        thread_kwargs = thread_class.call_args.kwargs
        thread_class.return_value.start.assert_called_once()
        self.assertIs(thread_kwargs['target'], send_mail)
        self.assertTrue(thread_kwargs['daemon'])

        mail_kwargs = thread_kwargs['kwargs']
        self.assertEqual(mail_kwargs['recipient_list'], [user.email])
        self.assertIn(user.username, mail_kwargs['message'])
        self.assertIn('https://student-performance-management-system-31uc.onrender.com', mail_kwargs['message'])
        reset_url = next(
            line for line in mail_kwargs['message'].splitlines()
            if line.startswith('https://')
        )
        response = self.client.get(urlparse(reset_url).path, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_confirm.html')

        uidb64, token = urlparse(reset_url).path.strip('/').split('/')[-2:]
        accounts_response = self.client.get(
            f'/accounts/reset/{uidb64}/{token}/',
            follow=True,
        )
        self.assertEqual(accounts_response.status_code, 200)
        self.assertTemplateUsed(
            accounts_response,
            'registration/password_reset_confirm.html',
        )

    def test_password_reset_complete_uses_registration_template(self):
        response = self.client.get('/reset/done/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_reset_complete.html')

    @patch('core.signals.Thread')
    def test_no_welcome_email_for_superuser_or_missing_email(self, thread_class):
        user_model = get_user_model()
        user_model.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin-password',
        )
        user_model.objects.create_user(
            username='noemail',
            email='',
            password='temporary-password',
        )

        thread_class.assert_not_called()
