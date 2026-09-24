from datetime import datetime
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.branches.models import Branch
from apps.dashboard.models import SiteSettings
from apps.reminders.models import SmsTemplate
from apps.reminders.serializers import SmsTemplateSerializer
from apps.reminders.tasks import _get_expiry_template, check_and_send_auto_sms


class AutomaticSmsTaskTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Test branch", code="TEST")
        self.settings = SiteSettings.get_for_branch(self.branch)
        self.settings.auto_sms_enabled = True
        self.settings.auto_sms_hour = 9
        self.settings.auto_sms_minute = 30
        self.settings.save()

    @patch("apps.reminders.tasks.send_expiry_reminders_for_branch.delay")
    @patch("apps.reminders.tasks.timezone.localtime")
    def test_dispatches_at_the_configured_minute(self, localtime, delay):
        localtime.return_value = timezone.make_aware(datetime(2026, 1, 1, 9, 30))

        check_and_send_auto_sms()

        delay.assert_called_once_with(str(self.branch.id))

    @patch("apps.reminders.tasks.send_expiry_reminders_for_branch.delay")
    @patch("apps.reminders.tasks.timezone.localtime")
    def test_does_not_dispatch_at_a_different_minute(self, localtime, delay):
        localtime.return_value = timezone.make_aware(datetime(2026, 1, 1, 9, 29))

        check_and_send_auto_sms()

        delay.assert_not_called()


class ExpiryTemplateSelectionTests(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(name="Branch template", code="BRANCH")

    def test_branch_template_takes_priority_over_global_template(self):
        global_template = SmsTemplate.objects.create(
            name="Global technical", body="Global", days_before=7, inspection_type="technical"
        )
        branch_template = SmsTemplate.objects.create(
            name="Branch technical", body="Branch", days_before=7,
            inspection_type="technical", branch=self.branch,
        )

        self.assertEqual(
            _get_expiry_template(7, "technical", self.branch).id,
            branch_template.id,
        )
        self.assertNotEqual(branch_template.id, global_template.id)

    def test_global_template_is_used_as_a_fallback(self):
        global_template = SmsTemplate.objects.create(
            name="Global any", body="Global", days_before=14, inspection_type="any"
        )

        self.assertEqual(
            _get_expiry_template(14, "gas_cylinder", self.branch).id,
            global_template.id,
        )


class SmsTemplateVariablesTests(TestCase):
    def test_legacy_aliases_are_rendered_for_automatic_sms(self):
        template = SmsTemplate(
            name="Legacy", body="{name} {client} {plate} {days} {date}", days_before=7
        )

        self.assertEqual(
            template.render(
                client_name="Ali", plate_number="01A123BC", days_left=7, expiry_date="01.02.2026"
            ),
            "Ali Ali 01A123BC 7 01.02.2026",
        )

    def test_unknown_variable_is_rejected_when_saving_template(self):
        serializer = SmsTemplateSerializer(data={
            "name": "Invalid", "body": "Salom {plate_no}", "inspection_type": "any"
        })

        self.assertFalse(serializer.is_valid())
        self.assertIn("body", serializer.errors)
