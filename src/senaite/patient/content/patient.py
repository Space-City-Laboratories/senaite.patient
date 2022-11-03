# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.PATIENT.
#
# SENAITE.PATIENT is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2020-2022 by it's authors.
# Some rights reserved, see README and LICENSE.

from six import string_types

from AccessControl import ClassSecurityInfo
from bika.lims import api
from bika.lims.api.mail import is_valid_email_address
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from Products.CMFCore import permissions
from senaite.core.api import dtime
from senaite.core.behaviors import IClientShareable
from senaite.core.schema import AddressField
from senaite.core.schema import DatetimeField
from senaite.core.schema.addressfield import OTHER_ADDRESS
from senaite.core.schema.addressfield import PHYSICAL_ADDRESS
from senaite.core.schema.addressfield import POSTAL_ADDRESS
from senaite.core.schema.fields import DataGridField
from senaite.core.schema.fields import DataGridRow
from senaite.core.z3cform.widgets.datagrid import DataGridWidgetFactory
from senaite.core.z3cform.widgets.datetimewidget import DatetimeWidget
from senaite.patient import api as patient_api
from senaite.patient import messageFactory as _
from senaite.patient.catalog import PATIENT_CATALOG
from senaite.patient.config import GENDERS
from senaite.patient.config import SEXES
from senaite.patient.interfaces import IPatient
from z3c.form.interfaces import NO_VALUE
from zope import schema
from zope.interface import Interface
from zope.interface import Invalid
from zope.interface import implementer
from zope.interface import invariant


class IIdentifiersSchema(Interface):
    """Schema definition for identifier records field
    """

    key = schema.Choice(
        title=_("Type"),
        description=_(
            u"The type of identifier that holds the ID"
        ),
        source="senaite.patient.vocabularies.identifiers",
        required=True,
    )

    value = schema.TextLine(
        title=_(u"ID"),
        description=_(
            u"The identification number of the selected identifier"
        ),
        required=True,
    )


class IAdditionalEmailSchema(Interface):
    """Schema definition for additional emails field
    """

    name = schema.TextLine(
        title=_("Name"),
        description=_(u"Private, Work, Other etc."),
        required=True,
    )

    email = schema.TextLine(
        title=_(u"Email"),
        description=_(u"Email address"),
        required=True,
    )


class IRaceSchema(Interface):
    """Schema definition for patient race
    """
    race = schema.Choice(
        title=_("Race"),
        description=_(u""),
        source="senaite.patient.vocabularies.races",
        required=False,
    )


class IEthnicitySchema(Interface):
    """Schema definition for patient ethnicity
    """
    ethnicity = schema.Choice(
        title=_("Ethnicity"),
        description=_(u""),
        source="senaite.patient.vocabularies.ethnicities",
        required=False,
    )


class IPatientSchema(model.Schema):
    """Patient Content
    """

    directives.omitted("title")
    title = schema.TextLine(
        title=u"Title",
        required=False
    )

    directives.omitted("description")
    description = schema.Text(
        title=u"Description",
        required=False
    )

    # race/ethnicity fieldset
    fieldset(
        "race_and_ethnicity",
        label=u"Race and Ethnicity",
        fields=["races", "ethnicities"])

    # contact fieldset
    fieldset(
        "contact",
        label=u"Contact",
        fields=["email", "additional_emails", "phone", "mobile"])

    # address fieldset
    fieldset(
        "address",
        label=u"Address",
        fields=["address"])

    # Default

    mrn = schema.TextLine(
        title=_(u"label_patient_mrn", default=u"Medical Record #"),
        description=_(u"Patient Medical Record Number"),
        required=True,
    )

    patient_id = schema.TextLine(
        title=_(u"label_patient_id", default=u"ID"),
        description=_(u"Unique Patient ID"),
        required=False,
    )

    directives.widget(
        "identifiers",
        DataGridWidgetFactory,
        auto_append=True)
    identifiers = DataGridField(
        title=_(u"Patient Identifiers"),
        description=_(
            u"Define one or more identifers for this patient"
        ),
        value_type=DataGridRow(
            title=u"Identifier",
            schema=IIdentifiersSchema),
        required=False,
        missing_value=[],
        default=[],
    )

    email_report = schema.Bool(
        title=_(
            u"label_patient_email_report",
            default=u"Email results report"),
        description=_(
            u"Add the patient email as CC recipient to new samples"),
        required=False,
        default=False,
    )

    firstname = schema.TextLine(
        title=_(u"label_patient_firstname", default=u"Firstname"),
        description=_(u"Patient firstname"),
        required=False,
    )

    middlename = schema.TextLine(
        title=_(u"label_patient_middlename", default=u"Middlename"),
        description=_(u"Patient middlename"),
        required=False,
    )

    lastname = schema.TextLine(
        title=_(u"label_patient_lastname", default=u"Lastname"),
        description=_(u"Patient lastname"),
        required=False,
    )

    sex = schema.Choice(
        title=_(u"label_patient_sex", default=u"Sex"),
        description=_(u"Patient sex at birth"),
        source="senaite.patient.vocabularies.sex",
        default="",
        required=True,
    )

    gender = schema.Choice(
        title=_(u"label_patient_gender", default=u"Gender Identity"),
        description=_(u"Patient gender identity"),
        source="senaite.patient.vocabularies.gender",
        default="",
        required=True,
    )

    directives.widget(
        "races",
        DataGridWidgetFactory,
        allow_reorder=True,
        auto_append=True)
    races = DataGridField(
        title=_(u"label_patient_races", default=u"Races"),
        description=_(
            "description_patient_races",
            default=u"General race category reported by the patient "
            u"- subject may have more than one"
        ),
        value_type=DataGridRow(schema=IRaceSchema),
        required=False,
        missing_value=[],
        default=[],
    )

    directives.widget(
        "ethnicities",
        DataGridWidgetFactory,
        allow_reorder=True,
        auto_append=True)
    ethnicities = DataGridField(
        title=_(u"label_patient_ethnicities", default=u"Ethnicities"),
        description=_(
            "description_patient_ethnicities",
            default=u"General ethnicity category reported by the patient "
            u"- subject may have more than one"
        ),
        value_type=DataGridRow(schema=IEthnicitySchema),
        required=False,
        missing_value=[],
        default=[],
    )

    # Contact

    # primary patient email address
    email = schema.TextLine(
        title=_(
            u"label_primary_patient_email",
            default=u"Primary Email"
        ),
        description=_(
            u"description_patient_primary_email",
            default=u"Primary email address for this patient"),
        required=False,
    )

    # additional emails
    directives.widget(
        "additional_emails",
        DataGridWidgetFactory,
        allow_reorder=True,
        auto_append=True)
    additional_emails = DataGridField(
        title=_(
            u"label_patient_additional_emails",
            default=u"Additional Emails"),
        description=_(
            u"description_patient_additional_emails",
            default=u"Additional email addresses for this patient"
        ),
        value_type=DataGridRow(
            title=u"Email",
            schema=IAdditionalEmailSchema),
        required=False,
        missing_value=[],
        default=[],
    )

    phone = schema.TextLine(
        title=_(u"label_patient_phone", default=u"Phone"),
        description=_(u"Patient phone number"),
        required=False,
    )

    mobile = schema.TextLine(
        title=_(u"label_patient_mobile", default=u"Mobile"),
        description=_(u"Patient mobile phone number"),
        required=False,
    )

    # Address
    address = AddressField(
        title=_("Address"),
        address_types=[
            PHYSICAL_ADDRESS,
            POSTAL_ADDRESS,
            OTHER_ADDRESS,
        ]
    )

    directives.widget("birthdate",
                      DatetimeWidget,
                      datepicker_nofuture=True,
                      show_time=False)
    birthdate = DatetimeField(
        title=_(u"label_patient_birthdate", default=u"Birthdate"),
        description=_(u"Patient birthdate"),
        required=False,
    )

    @invariant
    def validate_mrn(data):
        """Checks if the patient MRN # is unique
        """
        # https://community.plone.org/t/dexterity-unique-field-validation
        context = getattr(data, "__context__", None)
        if context is not None:
            if context.mrn == data.mrn:
                # nothing changed
                return

        if not data.mrn:
            raise Invalid(_("Patient Medical Record is missing or empty"))

        patient = patient_api.get_patient_by_mrn(
            data.mrn, full_object=False, include_inactive=True)

        if patient:
            raise Invalid(_("Patient Medical Record # must be unique"))

    @invariant
    def validate_patient_id(data):
        """Checks if the patient ID is unique
        """
        pid = data.patient_id

        # field is not required
        if not pid:
            return

        # https://community.plone.org/t/dexterity-unique-field-validation
        context = getattr(data, "__context__", None)
        if context is not None:
            if context.patient_id == pid:
                # nothing changed
                return

        query = {
            "portal_type": "Patient",
            "patient_id": pid,
            "is_active": True,
        }

        patient = patient_api.patient_search(query)

        if patient:
            raise Invalid(_("Patient ID must be unique"))

    @invariant
    def validate_email_report(data):
        """Checks if an email is set
        """
        value = data.email_report
        if not value:
            return

        # check if a valid email is in the request
        # Note: Workaround for missing `data.email`
        request = api.get_request()
        email = request.form.get("form.widgets.email")
        if email and is_valid_email_address(email):
            return

        # mark the request to avoid multiple raising
        key = "_v_email_report_checked"
        if getattr(request, key, False):
            return
        setattr(request, key, True)
        raise Invalid(_("Please set a valid email address first"))

    @invariant
    def validate_email(data):
        """Checks if the email is correct
        """
        if not data.email:
            return
        if not is_valid_email_address(data.email):
            raise Invalid(_("Patient email is invalid"))

    @invariant
    def validate_additional_emails(data):
        """Checks if the additional emails are valid
        """
        if not data.additional_emails:
            return
        for record in data.additional_emails:
            if record == NO_VALUE:
                continue
            email = record.get("email")
            if email and not is_valid_email_address(email):
                raise Invalid(_("Email address %s is invalid" % email))


@implementer(IPatient, IPatientSchema, IClientShareable)
class Patient(Container):
    """Results Interpretation Template content
    """
    _catalogs = [PATIENT_CATALOG]

    security = ClassSecurityInfo()

    @security.private
    def accessor(self, fieldname):
        """Return the field accessor for the fieldname
        """
        schema = api.get_schema(self)
        if fieldname not in schema:
            return None
        return schema[fieldname].get

    @security.private
    def mutator(self, fieldname):
        """Return the field mutator for the fieldname
        """
        schema = api.get_schema(self)
        if fieldname not in schema:
            return None
        return schema[fieldname].set

    @security.protected(permissions.View)
    def Title(self):
        return self.getFullname()

    @security.protected(permissions.View)
    def getMRN(self):
        """Returns the MRN with the field accessor
        """
        accessor = self.accessor("mrn")
        value = accessor(self) or ""
        return value.encode("utf-8")

    @security.protected(permissions.ModifyPortalContent)
    def setMRN(self, value):
        """Set MRN by the field accessor
        """
        # XXX These checks will be quite common on setters linked to `required`
        # fields. We could add a decorator or, if we use our own implementation
        # of BaseField, take this into consideration in the `get(self)` func.
        if not value:
            raise ValueError("Value is missing or empty")

        if not isinstance(value, string_types):
            raise ValueError("Type is not supported: {}".format(repr(value)))

        value = value.strip()
        accessor = self.accessor("mrn")
        if accessor(self) == api.safe_unicode(value):
            # Value has not changed
            return

        # Check if a patient with this same MRN already exists
        if patient_api.get_patient_by_mrn(value, full_object=False,
                                          include_inactive=True):
            raise ValueError("Value is not unique: {}".format(value))

        mutator = self.mutator("mrn")
        return mutator(self, api.safe_unicode(value))

    @security.protected(permissions.View)
    def getPatientID(self):
        """Returns the Patient ID with the field accessor
        """
        accessor = self.accessor("patient_id")
        value = accessor(self) or ""
        return value.encode("utf-8")

    @security.protected(permissions.ModifyPortalContent)
    def setPatientID(self, value):
        """Set Patient ID by the field accessor
        """
        if not isinstance(value, string_types):
            value = u""
        if value:
            value = value.strip()
            query = {"portal_type": "Patient", "patient_id": value}
            results = patient_api.patient_search(query)
            if len(results) > 0:
                raise ValueError("A patient with that ID already exists!")

        mutator = self.mutator("patient_id")
        mutator(self, api.safe_unicode(value.strip()))

    @security.protected(permissions.View)
    def getIdentifiers(self):
        """Returns the identifiers with the field accessor
        """
        accessor = self.accessor("identifiers")
        return accessor(self)

    def get_identifier_items(self):
        """Returns a list of identifier tuples
        """
        identifiers = self.getIdentifiers()
        return list(map(lambda i: (i["key"], i["value"]), identifiers))

    def get_identifier_ids(self):
        """Returns a list of identifier IDs
        """
        identifiers = self.getIdentifiers()
        return list(map(lambda i: i["value"], identifiers))

    @security.protected(permissions.ModifyPortalContent)
    def setIdentifiers(self, value):
        """Set identifiers by the field accessor
        """
        mutator = self.mutator("identifiers")
        return mutator(self, value)

    @security.protected(permissions.View)
    def getRaces(self):
        """Returns the patient races
        """
        accessor = self.accessor("races")
        return accessor(self)

    @security.protected(permissions.ModifyPortalContent)
    def setRaces(self, value):
        """Set the patient races
        """
        mutator = self.mutator("races")
        return mutator(self, value)

    @security.protected(permissions.View)
    def getEthnicities(self):
        """Returns the patient ethnicities
        """
        accessor = self.accessor("ethnicities")
        return accessor(self)

    @security.protected(permissions.ModifyPortalContent)
    def setEthnicities(self, value):
        """Set the patient ethnicities
        """
        mutator = self.mutator("ethnicities")
        return mutator(self, value)

    @security.protected(permissions.View)
    def getEmailReport(self):
        """Returns the email report option
        """
        accessor = self.accessor("email_report")
        return accessor(self)

    @security.protected(permissions.ModifyPortalContent)
    def setEmailReport(self, value):
        """Set the email report option
        """
        mutator = self.mutator("email_report")
        return mutator(self, value)

    @security.protected(permissions.View)
    def getFirstname(self):
        accessor = self.accessor("firstname")
        value = accessor(self) or ""
        return value.encode("utf-8")

    @security.protected(permissions.ModifyPortalContent)
    def setFirstname(self, value):
        if not isinstance(value, string_types):
            value = u""
        mutator = self.mutator("firstname")
        mutator(self, api.safe_unicode(value.strip()))

    @security.protected(permissions.View)
    def getMiddlename(self):
        accessor = self.accessor("middlename")
        value = accessor(self) or ""
        return value.encode("utf-8")

    @security.protected(permissions.ModifyPortalContent)
    def setMiddlename(self, value):
        if not isinstance(value, string_types):
            value = u""
        mutator = self.mutator("middlename")
        mutator(self, api.safe_unicode(value.strip()))

    @security.protected(permissions.View)
    def getLastname(self):
        accessor = self.accessor("lastname")
        value = accessor(self) or ""
        return value.encode("utf-8")

    @security.protected(permissions.ModifyPortalContent)
    def setLastname(self, value):
        if not isinstance(value, string_types):
            value = u""
        mutator = self.mutator("lastname")
        mutator(self, api.safe_unicode(value.strip()))

    @security.protected(permissions.View)
    def getFullname(self):
        # Create the fullname from firstname + middlename + lastname
        parts = [self.getFirstname(), self.getMiddlename(), self.getLastname()]
        return " ".join(filter(None, parts))

    @security.protected(permissions.View)
    def getEmail(self):
        """Returns the email with the field accessor
        """
        accessor = self.accessor("email")
        value = accessor(self) or ""
        return value.encode("utf-8")

    @security.protected(permissions.ModifyPortalContent)
    def setEmail(self, value):
        """Set email by the field accessor
        """
        if not isinstance(value, string_types):
            value = u""
        mutator = self.mutator("email")
        mutator(self, api.safe_unicode(value.strip()))

    @security.protected(permissions.View)
    def getAdditionalEmails(self):
        """Returns the email with the field accessor
        """
        accessor = self.accessor("additional_emails")
        return accessor(self) or []

    @security.protected(permissions.ModifyPortalContent)
    def setAdditionalEmails(self, value):
        """Set email by the field accessor
        """
        mutator = self.mutator("additional_emails")
        mutator(self, value)

    @security.protected(permissions.View)
    def getSex(self):
        """Returns the sex with the field accessor
        """
        accessor = self.accessor("sex")
        return accessor(self)

    @security.protected(permissions.View)
    def getSexText(self):
        """Returns the sex with the field accessor
        """
        sexes = dict(SEXES)
        value = self.getSex()
        value = sexes.get(value)
        return value.encode("utf-8")

    @security.protected(permissions.ModifyPortalContent)
    def setSex(self, value):
        """Set sex by the field accessor
        """
        for k, v in SEXES:
            if value == v:
                value = k
        mutator = self.mutator("sex")
        mutator(self, api.safe_unicode(value))

    @security.protected(permissions.View)
    def getGender(self):
        """Returns the gender with the field accessor
        """
        accessor = self.accessor("gender")
        return accessor(self)

    @security.protected(permissions.View)
    def getGenderText(self):
        """Returns the gender with the field accessor
        """
        genders = dict(GENDERS)
        value = self.getGender()
        value = genders.get(value)
        return value.encode("utf-8")

    @security.protected(permissions.ModifyPortalContent)
    def setGender(self, value):
        """Set birthdate by the field accessor
        """
        for k, v in GENDERS:
            if value == v:
                value = k
        mutator = self.mutator("gender")
        mutator(self, api.safe_unicode(value))

    @security.protected(permissions.View)
    def getBirthdate(self, as_date=True):
        """Returns the birthday with the field accessor
        """
        accessor = self.accessor("birthdate")
        value = accessor(self)
        # Return a plain date object to avoid timezone issues
        if dtime.is_dt(value) and as_date:
            value = value.date()
        return value

    @security.protected(permissions.ModifyPortalContent)
    def setBirthdate(self, value):
        """Set birthdate by the field accessor
        """
        mutator = self.mutator("birthdate")
        return mutator(self, value)

    @security.protected(permissions.View)
    def getAddress(self):
        """Returns the address with the field accessor
        """
        accessor = self.accessor("address")
        return accessor(self)

    @security.protected(permissions.ModifyPortalContent)
    def setAddress(self, value):
        """Set address by the field accessor
        """
        mutator = self.mutator("address")
        return mutator(self, value)
