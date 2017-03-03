from tests.integration.create_token import create_token
from tests.integration.integration_test_case import IntegrationTestCase


class TestLogin(IntegrationTestCase):

    def test_login_with_no_token_should_be_unauthorized(self):
        # Given
        token = ""

        # When
        resp = self.client.get('/session?token=' + token, follow_redirects=False)

        # Then
        self.assertEqual(resp.status_code, 401)

    def test_login_with_invalid_token_should_be_forbidden(self):
        # Given
        token = "123"

        # When
        resp = self.client.get('/session?token=' + token, follow_redirects=False)

        # Then
        self.assertEqual(resp.status_code, 403)

    def test_login_with_valid_token_should_redirect_to_survey(self):
        # Given
        token = create_token('0205', '1')

        # When
        resp = self.client.get('/session?token=' + token.decode(), follow_redirects=False)

        # Then
        self.assertEqual(resp.status_code, 302)
        self.assertRegex(resp.location, '/questionnaire/1/0205')

    def test_login_with_token_twice_is_unauthorised_when_same_jti_provided(self):
        # Given
        token = create_token('0205', '1')
        self.client.get('/session?token=' + token.decode(), follow_redirects=False)

        # When
        resp = self.client.get('/session?token=' + token.decode(), follow_redirects=False)

        # Then
        self.assertEqual(resp.status_code, 401)

    def test_login_with_token_twice_is_authorised_when_no_jti(self):
        # Given
        token = create_token('0205', '1', jti=None)
        self.client.get('/session?token=' + token.decode(), follow_redirects=False)

        # When
        resp = self.client.get('/session?token=' + token.decode(), follow_redirects=False)

        # Then
        self.assertEqual(resp.status_code, 302)
