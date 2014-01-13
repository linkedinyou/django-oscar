# -*- coding: utf-8 -*-
from django.test import TestCase
from django.core import exceptions

from nose.tools import raises

from oscar.apps.order.models import ShippingAddress
from oscar.core.compat import get_user_model
from oscar.apps.address import models


User = get_user_model()


class TestUserAddress(TestCase):

    def setUp(self):
        self.country = models.Country(
            iso_3166_1_a2='GB', name="UNITED KINGDOM")

    def test_uses_title_firstname_and_lastname_in_salutation(self):
        a = models.UserAddress(
            title="Dr",
            first_name="Barry",
            last_name='Barrington')
        self.assertEquals("Dr Barry Barrington", a.salutation)

    def test_strips_whitespace_from_salutation(self):
        a = models.UserAddress(last_name='Barrington')
        self.assertEquals("Barrington", a.salutation)

    def test_has_name_property(self):
        a = models.UserAddress(
            title="Dr",
            first_name="Barry",
            last_name='Barrington')
        self.assertEquals("Barry Barrington", a.name)

    def test_has_summary_property(self):
        a = models.UserAddress(
            title="Dr",
            first_name="Barry",
            last_name='Barrington',
            line1="1 King Road",
            line4="London",
            postcode="SW1 9RE")
        self.assertEquals("Dr Barry Barrington, 1 King Road, London, SW1 9RE",
                          a.summary)

    def test_summary_includes_country(self):
        c = models.Country(
            pk=1, iso_3166_1_a2="GB", name="UNITED KINGDOM")
        a = models.UserAddress(
            title="Dr",
            first_name="Barry",
            last_name='Barrington',
            line1="1 King Road",
            line4="London",
            postcode="SW1 9RE",
            country=c)
        self.assertEquals(
            "Dr Barry Barrington, 1 King Road, London, SW1 9RE, UNITED KINGDOM",
            a.summary)

    def test_can_be_hashed(self):
        a = models.UserAddress(
            title="Dr",
            first_name="Barry",
            last_name='Barrington',
            line1="1 King Road",
            line4="London",
            postcode="SW1 9RE")
        hash = a.generate_hash()
        self.assertTrue(hash is not None)

    def test_can_be_hashed_including_non_ascii(self):
        a = models.UserAddress(
            first_name=u"\u0141ukasz Smith",
            last_name=u'Smith',
            line1=u"75 Smith Road",
            postcode=u"n4 8ty")
        hash = a.generate_hash()
        self.assertTrue(hash is not None)

    def test_strips_whitespace_in_name_property(self):
        a = models.UserAddress(
            last_name='Barrington')
        self.assertEquals("Barrington", a.name)

    def test_uses_city_as_an_alias_of_line4(self):
        a = models.UserAddress(
            last_name='Barrington',
            line1="75 Smith Road",
            line4="London",
            postcode="n4 8ty")
        self.assertEqual('London', a.city)

    def test_converts_postcode_to_uppercase_when_cleaning(self):
        address = models.UserAddress(
            last_name='Barrington',
            line1="75 Smith Road",
            postcode="n4 8ty",
            country=self.country)
        address.clean()
        self.assertEquals("N4 8TY", address.postcode)

    def test_strips_whitespace_when_cleaning(self):
        a = models.UserAddress(
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        a.clean()
        self.assertEquals("N4 8TY", a.postcode)
        self.assertEquals("75 Smith Road", a.line1)

    def test_active_address_fields_skips_whitespace_only_fields(self):
        a = models.UserAddress(
            first_name="   ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        active_fields = a.active_address_fields()
        self.assertEquals("Barrington", active_fields[0])

    def test_ignores_whitespace_when_hashing(self):
        a1 = models.UserAddress(
            first_name=" Terry  ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        a1.clean()
        a2 = models.UserAddress(
            first_name=" Terry",
            last_name='   Barrington',
            line1="  75 Smith Road  ",
            postcode="N4 8ty",
            country=self.country)
        a2.clean()
        self.assertEquals(a1.generate_hash(), a2.generate_hash())

    def test_populate_shipping_address_doesnt_set_id(self):
        a = models.UserAddress(
            first_name=" Terry  ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        a.clean()
        sa = ShippingAddress()
        a.populate_alternative_model(sa)
        self.assertIsNone(sa.id)

    def test_populated_shipping_address_has_same_summary_user_address(self):
        a = models.UserAddress(
            first_name=" Terry  ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        a.clean()
        sa = ShippingAddress()
        a.populate_alternative_model(sa)
        self.assertEquals(sa.summary, a.summary)

    def test_summary_is_property(self):
        a = models.UserAddress(
            first_name=" Terry  ",
            last_name='Barrington',
            line1="  75 Smith Road  ",
            postcode="  n4 8ty",
            country=self.country)
        a.clean()
        self.assertEquals(
            u"Terry Barrington, 75 Smith Road, N4 8TY, UNITED KINGDOM",
            a.summary)

VALID_POSTCODES = [
    ('GB', 'N1 9RT'),
    ('SK', '991 41'),
    ('CZ', '612 00'),
    ('CC', '6799'),
    ('CY', '8240'),
    ('MC', '98000'),
    ('SH', 'STHL 1ZZ'),
    ('JP', '150-2345'),
    ('PG', '314'),
    ('HN', '41202'),
    # It works for small cases as well
    ('GB', 'sw2 1rw'),
]


INVALID_POSTCODES = [
    ('GB', 'not-a-postcode'),
    ('DE', '123b4'),
]


def assert_valid_postcode(country_value, postcode_value):
    country = models.Country(iso_3166_1_a2=country_value)
    address = models.UserAddress(country=country, postcode=postcode_value)
    address.clean()


@raises(exceptions.ValidationError)
def assert_invalid_postcode(country_value, postcode_value):
    country = models.Country(iso_3166_1_a2=country_value)
    address = models.UserAddress(country=country, postcode=postcode_value)
    address.clean()


def test_postcode_is_validated_for_country():
    for country, postcode in VALID_POSTCODES:
        yield assert_valid_postcode, country, postcode


def test_postcode_is_only_valid():
    for country, postcode in INVALID_POSTCODES:
        yield assert_invalid_postcode, country, postcode