from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, DecimalField,IntegerField, SelectField,RadioField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Optional, NumberRange
from enum import Enum
from dataclasses import dataclass
import math
from flask import render_template, request, redirect, url_for
class Currency(Enum):
    AED = 'AED'
    USD = 'USD'


class AssetIdentForm(FlaskForm):
    enter_area = SelectField('Enter Area:', validators=[DataRequired()])
    property_usage = SelectField('Property Usage:', validators=[DataRequired()])
    property_type = SelectField('Property Type:', validators=[DataRequired()])
    property_sub_type = SelectField('Property Subtype:', validators=[DataRequired()])
    price_from = DecimalField('From:', validators=[Optional(), NumberRange(min=0)])
    price_to = DecimalField('To:', validators=[Optional(), NumberRange(min=0)])
    select_one = RadioField('', validators=[DataRequired(message="Please select one option")])

    desired_min_capital_appreciation = DecimalField('Desired Minimum Capital Appreciation in the next 5 years (%):', validators=[Optional(), NumberRange(min=0, max=100)])
    desired_min_gross_rental_yield = DecimalField('Desired Minimum Gross Rental Yield (%):', validators=[Optional(), NumberRange(min=0, max=100)])
    high_demand_projects_only = SelectField('High Demand Projects Only:', choices=[('Yes', 'Yes'), ('No', 'No')], validators=[Optional()])

    def validate(self, extra_validators=None):
        if not super(AssetIdentForm, self).validate(extra_validators=extra_validators):
            return False

        valid = True
        select_one = self.select_one.data

        if not select_one:
            self.select_one.errors.append('Please select one option')
            valid = False
        elif select_one == 'high_growth':
            if not self.desired_min_capital_appreciation.data:
                self.desired_min_capital_appreciation.errors.append('This field is required.')
                valid = False
        elif select_one == 'high_yield':
            if not self.desired_min_gross_rental_yield.data:
                self.desired_min_gross_rental_yield.errors.append('This field is required.')
                valid = False
        # For 'distressed', fields are optional
        return valid