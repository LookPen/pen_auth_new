from django.test import TestCase
import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pen_auth.settings")

from oauth_pen.settings import OAuthPenSetting

if __name__ == '__main__':
    val = OAuthPenSetting.import_from_string('oauth_pen.exceptions.ErrorConfigException')
    print(val)
