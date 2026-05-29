"""
Test cases for core app - Landing page and email utilities
"""
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from core.email_utils import (
    send_email,
    send_zeptomail_email,
    _parse_recipients,
    _parse_from_address,
    _prepare_body_content,
    _get_api_config,
    _build_attachments
)


class LandingPageTests(TestCase):
    """Test landing page functionality"""
    
    def setUp(self):
        self.client = Client()
        self.index_url = reverse('core:index')
    
    def test_landing_page_loads(self):
        """Test landing page renders successfully"""
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/index.html')
    
    def test_landing_page_contains_services(self):
        """Test landing page contains service information"""
        response = self.client.get(self.index_url)
        
        # Check for service mentions (in HTML content)
        content = response.content.decode('utf-8')
        self.assertIn('Basic', content)
        self.assertIn('Cleaning', content)


class EmailUtilsTests(TestCase):
    """Test email utility functions"""
    
    def test_parse_recipients_single_email(self):
        """Test parsing single email address"""
        recipients = _parse_recipients('test@example.com')
        
        self.assertEqual(len(recipients), 1)
        self.assertEqual(recipients[0]['email_address']['address'], 'test@example.com')
    
    def test_parse_recipients_with_name(self):
        """Test parsing email with display name"""
        recipients = _parse_recipients('Test User <test@example.com>')
        
        self.assertEqual(len(recipients), 1)
        self.assertEqual(recipients[0]['email_address']['address'], 'test@example.com')
        self.assertEqual(recipients[0]['email_address']['name'], 'Test User')
    
    def test_parse_recipients_list(self):
        """Test parsing list of email addresses"""
        emails = ['user1@example.com', 'User Two <user2@example.com>']
        recipients = _parse_recipients(emails)
        
        self.assertEqual(len(recipients), 2)
        self.assertEqual(recipients[0]['email_address']['address'], 'user1@example.com')
        self.assertEqual(recipients[1]['email_address']['address'], 'user2@example.com')
    
    def test_parse_recipients_invalid_quiet(self):
        """Test parsing invalid email with quiet mode"""
        recipients = _parse_recipients('invalid-email', quiet=True)
        
        # Should return empty list without raising exception
        self.assertEqual(recipients, [])
    
    @patch('core.email_utils.settings')
    def test_parse_from_address(self, mock_settings):
        """Test parsing from address"""
        mock_settings.DEFAULT_FROM_EMAIL = 'Sneaky Klean <noreply@sneakyklean.com>'
        
        from_obj = _parse_from_address()
        
        self.assertEqual(from_obj['address'], 'noreply@sneakyklean.com')
        self.assertEqual(from_obj['name'], 'Sneaky Klean')
    
    def test_prepare_body_content_text_only(self):
        """Test preparing body with only text"""
        text, html = _prepare_body_content('Hello World', '')
        
        self.assertEqual(text, 'Hello World')
        self.assertEqual(html, '<p>Hello World</p>')
    
    def test_prepare_body_content_html_only(self):
        """Test preparing body with only HTML"""
        text, html = _prepare_body_content('', '<h1>Hello</h1>')
        
        self.assertTrue(len(text) > 0)  # Should generate text fallback
        self.assertEqual(html, '<h1>Hello</h1>')
    
    def test_prepare_body_content_both(self):
        """Test preparing body with both text and HTML"""
        text, html = _prepare_body_content('Plain text', '<p>HTML content</p>')
        
        self.assertEqual(text, 'Plain text')
        self.assertEqual(html, '<p>HTML content</p>')
    
    @patch('core.email_utils.settings')
    def test_get_api_config_success(self, mock_settings):
        """Test getting API config with valid settings"""
        mock_settings.ZEPTO_API_KEY = 'test-api-key'
        mock_settings.ZEPTO_API_BASE_URL = 'https://api.zeptomail.com/v1.1'
        
        url, api_key, headers = _get_api_config(quiet=True)
        
        self.assertIsNotNone(url)
        self.assertEqual(api_key, 'test-api-key')
        self.assertIn('Authorization', headers)
        self.assertIn('Zoho-enczapikey test-api-key', headers['Authorization'])
    
    @patch('core.email_utils.settings')
    def test_get_api_config_missing(self, mock_settings):
        """Test getting API config with missing settings"""
        mock_settings.ZEPTO_API_KEY = None
        mock_settings.ZEPTO_API_BASE_URL = ''
        
        result = _get_api_config(quiet=True)
        
        # Should return None values when config is missing
        self.assertEqual(result, (None, None, None))
    
    def test_build_attachments_with_file(self):
        """Test building attachments"""
        attachments = [
            ('test.txt', b'Hello World', 'text/plain')
        ]
        
        api_attachments = _build_attachments(attachments)
        
        self.assertEqual(len(api_attachments), 1)
        self.assertEqual(api_attachments[0]['name'], 'test.txt')
        self.assertEqual(api_attachments[0]['mime_type'], 'text/plain')
        self.assertIn('content', api_attachments[0])
    
    def test_build_attachments_empty(self):
        """Test building with no attachments"""
        api_attachments = _build_attachments(None)
        
        self.assertEqual(api_attachments, [])
    
    @patch('core.email_utils.requests.post')
    @patch('core.email_utils.settings')
    def test_send_zeptomail_email_success(self, mock_settings, mock_post):
        """Test sending email via ZeptoMail API successfully"""
        # Mock settings
        mock_settings.ZEPTO_API_KEY = 'test-key'
        mock_settings.ZEPTO_API_BASE_URL = 'https://api.test.com'
        mock_settings.DEFAULT_FROM_EMAIL = 'Test <test@test.com>'
        
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'message': 'success'}
        mock_post.return_value = mock_response
        
        result = send_zeptomail_email(
            recipients='recipient@example.com',
            subject='Test Email',
            body_text='Test body',
            body_html='<p>Test body</p>',
            quiet=False
        )
        
        # Should succeed
        self.assertIsNotNone(result)
        mock_post.assert_called_once()
    
    @patch('core.email_utils.requests.post')
    @patch('core.email_utils.settings')
    def test_send_zeptomail_email_api_error(self, mock_settings, mock_post):
        """Test sending email with API error"""
        # Mock settings
        mock_settings.ZEPTO_API_KEY = 'test-key'
        mock_settings.ZEPTO_API_BASE_URL = 'https://api.test.com'
        mock_settings.DEFAULT_FROM_EMAIL = 'Test <test@test.com>'
        
        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Error message'
        mock_post.return_value = mock_response
        
        result = send_zeptomail_email(
            recipients='recipient@example.com',
            subject='Test Email',
            body_text='Test body',
            quiet=True  # Don't raise exception
        )
        
        # Should return None on error with quiet=True
        self.assertIsNone(result)
    
    @patch('core.email_utils.send_zeptomail_email')
    def test_send_email_wrapper(self, mock_send):
        """Test send_email wrapper function"""
        mock_send.return_value = {'message': 'success'}
        
        result = send_email(
            recipient='test@example.com',
            subject='Test',
            body_text='Test body',
            body_html='<p>Test</p>'
        )
        
        # Mock should be called
        mock_send.assert_called_once()
        
        # Check arguments passed
        call_kwargs = mock_send.call_args[1]
        self.assertEqual(call_kwargs['recipients'], 'test@example.com')
        self.assertEqual(call_kwargs['subject'], 'Test')
    
    @patch('core.email_utils.send_zeptomail_email')
    def test_send_email_generates_html_from_text(self, mock_send):
        """Test send_email generates HTML from text if not provided"""
        send_email(
            recipient='test@example.com',
            subject='Test',
            body_text='Plain text body'
            # No body_html provided
        )
        
        # Check that HTML was generated
        call_kwargs = mock_send.call_args[1]
        self.assertIn('<p>Plain text body</p>', call_kwargs['body_html'])


class EmailIntegrationTests(TestCase):
    """Integration tests for email system"""
    
    @patch('core.email_utils.requests.post')
    @patch('core.email_utils.settings')
    def test_full_email_sending_flow(self, mock_settings, mock_post):
        """Test complete email sending flow"""
        # Mock settings
        mock_settings.ZEPTO_API_KEY = 'test-api-key'
        mock_settings.ZEPTO_API_BASE_URL = 'https://api.zeptomail.com/v1.1'
        mock_settings.DEFAULT_FROM_EMAIL = 'Sneaky Klean <noreply@sneakyklean.com>'
        
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'message': 'Email sent successfully',
            'request_id': 'test-123'
        }
        mock_post.return_value = mock_response
        
        # Send email
        result = send_email(
            recipient='customer@example.com',
            subject='Your Order Confirmation',
            body_text='Thank you for your order!',
            body_html='<h1>Thank you for your order!</h1>',
            quiet=False
        )
        
        # Verify API was called
        self.assertTrue(mock_post.called)
        
        # Verify API call parameters
        call_args = mock_post.call_args
        
        # Check URL
        self.assertIn('zeptomail', call_args[0][0])
        
        # Check payload structure
        payload = call_args[1]['json']
        self.assertIn('from', payload)
        self.assertIn('to', payload)
        self.assertIn('subject', payload)
        self.assertEqual(payload['subject'], 'Your Order Confirmation')
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result['message'], 'Email sent successfully')
