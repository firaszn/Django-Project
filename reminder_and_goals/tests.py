from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Reminder, Goal

class ReminderAndGoalTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.reminder = Reminder.objects.create(
            user=self.user,
            title='Test Reminder',
            description='This is a test reminder.',
            reminder_time='20:00:00',
            status=True
        )
        self.goal = Goal.objects.create(
            user=self.user,
            title='Test Goal',
            description='This is a test goal.',
            target=5,
            progress=2,
            start_date='2025-10-01',
            end_date='2025-10-31'
        )

    def test_reminder_list_view(self):
        response = self.client.get(reverse('reminder_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Reminder')

    def test_goal_list_view(self):
        response = self.client.get(reverse('goal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Goal')

    def test_reminder_create_view(self):
        response = self.client.post(reverse('reminder_create'), {
            'title': 'New Reminder',
            'description': 'New reminder description.',
            'reminder_time': '21:00:00',
            'status': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Reminder.objects.filter(user=self.user).last().title, 'New Reminder')

    def test_goal_create_view(self):
        response = self.client.post(reverse('goal_create'), {
            'title': 'New Goal',
            'description': 'New goal description.',
            'target': 10,
            'start_date': '2025-10-01',
            'end_date': '2025-10-31'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Goal.objects.filter(user=self.user).last().title, 'New Goal')

    def test_reminder_delete_view(self):
        response = self.client.post(reverse('reminder_delete', args=[self.reminder.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Reminder.objects.filter(id=self.reminder.id).exists())

    def test_goal_delete_view(self):
        response = self.client.post(reverse('goal_delete', args=[self.goal.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Goal.objects.filter(id=self.goal.id).exists())