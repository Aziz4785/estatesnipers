from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, SelectField,RadioField, BooleanField, FieldList, FormField
from wtforms.validators import DataRequired, Optional
from enum import Enum
from dataclasses import dataclass

class FinancingOption(Enum):
    MORTGAGE = 'mortgage'
    PAYMENT_PLAN = 'paymentPlan'
    NONE = 'none'

class Currency(Enum):
    AED = 'AED'
    USD = 'USD'

class InstalmentPlan:
    def __init__(self, percentage, duration):
        self.percentage = percentage
        self.duration = duration
    def __str__(self):
        return f"Percentage: {self.percentage}, Duration: {self.duration}"

class InstalmentPlanForm(FlaskForm):
    percentage = FloatField('In Percentage of asking price:', validators=[Optional()])
    duration = IntegerField('Duration (months):', validators=[Optional()])
    
    def create_object(self):
        return InstalmentPlan(self.percentage.data, self.duration.data)

class Property:
    def __init__(self, project_name, property_usage, property_type, property_sub_type,
                 property_area, area_unit, asking_price,
                 requires_repair, repair_fees, value_after_repair, gross_rental_yield, 
                 gross_rental_yield_unit, annual_increase, annual_op_expenses, annual_op_expenses_unit,
                onetime_acq_fee, fee_unit, financing_option, mortgage_annual_ir=None, mortgage_downpayment=None, mortgage_downpayment_unit=None,
                 mortgage_length=None, mortgage_length_unit=None,
                 plan_downpayment=None, plan_downpayment_unit=None, instalment_plans=None,
                 settlement_on_handover=None,settlement_percentage=None,settlement_duration=None,post_handover=None,post_handover_percentage=None,post_handover_duration=None,
                 cashflow_analysis_period=None,annual_capital_appreciation=None):
        self.project_name = project_name
        self.property_usage = property_usage
        self.property_type = property_type
        self.property_sub_type = property_sub_type
        self.property_area = property_area
        self.area_unit = area_unit
        self.asking_price = asking_price
        self.requires_repair = requires_repair
        self.repair_fees = repair_fees
        self.value_after_repair = value_after_repair
        self.gross_rental_yield = gross_rental_yield
        self.gross_rental_yield_unit = gross_rental_yield_unit
        self.annual_increase = annual_increase
        self.annual_op_expenses = annual_op_expenses
        self.annual_op_expenses_unit = annual_op_expenses_unit
        self.onetime_acq_fee = onetime_acq_fee
        self.fee_unit = fee_unit
        self.financing_option = financing_option

        # Mortgage fields
        self.mortgage_annual_ir = mortgage_annual_ir
        self.mortgage_downpayment = mortgage_downpayment
        self.mortgage_downpayment_unit = mortgage_downpayment_unit
        self.mortgage_length = mortgage_length
        self.mortgage_length_unit = mortgage_length_unit
        
        # Payment plan fields
        self.plan_downpayment = plan_downpayment
        self.plan_downpayment_unit = plan_downpayment_unit
        self.instalment_plans = instalment_plans or []

        self.settlement_on_handover = settlement_on_handover
        self.settlement_percentage = settlement_percentage
        self.settlement_duration = settlement_duration
        self.post_handover = post_handover
        self.post_handover_percentage = post_handover_percentage
        self.post_handover_duration = post_handover_duration
        self.cashflow_analysis_period = cashflow_analysis_period
        self.annual_capital_appreciation = annual_capital_appreciation

    def __str__(self):
        return f"Project Name: {self.project_name}, Property Usage: {self.property_usage}, Property Type: {self.property_type}, Property Subtype: {self.property_sub_type}, Property Area: {self.property_area}, Area Unit: {self.area_unit}, Asking Price: {self.asking_price}, Requires Repair: {self.requires_repair}, Repair Fees: {self.repair_fees}, Value After Repair: {self.value_after_repair}, Gross Rental Yield: {self.gross_rental_yield}, Gross Rental Yield Unit: {self.gross_rental_yield_unit}, Annual Increase: {self.annual_increase}, Annual Op Expenses: {self.annual_op_expenses}, Annual Op Expenses Unit: {self.annual_op_expenses_unit}, Onetime Acq Fee: {self.onetime_acq_fee}, Fee Unit: {self.fee_unit}, Financing Option: {self.financing_option}, Mortgage Annual IR: {self.mortgage_annual_ir}, Mortgage Downpayment: {self.mortgage_downpayment}, Mortgage Downpayment Unit: {self.mortgage_downpayment_unit}, Mortgage Length: {self.mortgage_length}, Mortgage Length Unit: {self.mortgage_length_unit}, Plan Downpayment: {self.plan_downpayment}, Plan Downpayment Unit: {self.plan_downpayment_unit}, Instalment Plans: {self.instalment_plans}, Settlement On Handover: {self.settlement_on_handover}, Settlement Percentage: {self.settlement_percentage}, Settlement Duration: {self.settlement_duration}, Post Handover: {self.post_handover}, Post Handover Percentage: {self.post_handover_percentage}, Post Handover Duration: {self.post_handover_duration}, Cashflow Analysis Period: {self.cashflow_analysis_period}, Annual Capital Appreciation: {self.annual_capital_appreciation}"

    def compute(self):
        table = {}
        for i in range(1, self.cashflow_analysis_period + 1):
            table[i] = {
                'gross_rental_yield': None,
                'OPEX': None,
                'AP': None,
                'cumulative_AP': None,
                'Expenses': None,
                'V': None, #property market value,
                'CF': None, #cashflow
                'CoC': None, #cash on cash return
                'Cumulative_CF': None, #cumulative cashflow
                'ROI': None, #return on investment
                'OM': None, #outstanding mortgage
                'Equity_currency': None, #equity in currency
                'Equity_percent': None, #equity in percentage
                'ROE': None, #return on equity
                'total_cash_invested': 0,
            }
        table[0] = {
            'V': None, #property market value,
        }
        if self.requires_repair == 'yes':
            table[0]['V'] = self.value_after_repair
        else:
            table[0]['V'] = self.asking_price

        #CONSTANTS:
        downpayment_currency = None
        if self.financing_option == FinancingOption.MORTGAGE:
            if self.mortgage_downpayment_unit == 'percent':
                downpayment_currency = self.mortgage_downpayment * self.asking_price / 100
            elif self.mortgage_downpayment_unit == 'usd' or self.mortgage_downpayment_unit == 'aed':
                downpayment_currency = self.mortgage_downpayment
        elif self.financing_option == FinancingOption.PAYMENT_PLAN:
            if self.plan_downpayment_unit == 'percent':
                downpayment_currency = self.plan_downpayment * self.asking_price / 100
            elif self.plan_downpayment_unit == 'usd' or self.plan_downpayment_unit == 'aed':
                downpayment_currency = self.plan_downpayment


       


        principle = None
        monthly_interest_rate = None
        total_number_of_payments = None
        monthly_mortgage_payment = None
        yearly_mortgage_payment = None
        mortgage_length_in_years = None
        if self.financing_option == FinancingOption.MORTGAGE:
            if self.mortgage_length_unit == 'years':
                mortgage_length_in_years = self.mortgage_length
            elif self.mortgage_length_unit == 'months':
                mortgage_length_in_years = self.mortgage_length / 12
            principle = self.asking_price - downpayment_currency
            monthly_interest_rate = self.mortgage_annual_ir / 12
            total_number_of_payments = mortgage_length_in_years * 12
            #monthly_mortgage_payment = principle * monthly_interest_rate / (1 - (1 + monthly_interest_rate) ** -total_number_of_payments)
            monthly_mortgage_payment = principle * monthly_interest_rate * (1 + monthly_interest_rate) ** total_number_of_payments / ((1 + monthly_interest_rate) ** total_number_of_payments - 1)
            yearly_mortgage_payment = monthly_mortgage_payment * 12


        OTF_currency = None
        if self.fee_unit == 'percent':
            OTF_currency = self.onetime_acq_fee * self.asking_price / 100
        elif self.fee_unit == 'usd' or self.fee_unit == 'aed':
            OTF_currency = self.onetime_acq_fee

        avg_annual_increase_percentage = self.annual_increase

        REP = self.repair_fees
        CA = self.annual_capital_appreciation
        if REP is None:
            REP = 0
        #VARIABLES:


        total_instalment_duration = 0
        start_i = 0
        residual = 0
        for year in range(1,self.cashflow_analysis_period + 1):
            sum_instalment_percentage = 0
            if year == 1:
                table[year]['gross_rental_yield'] = None
                if self.gross_rental_yield_unit == 'percent':
                    table[year]['gross_rental_yield'] = self.gross_rental_yield * self.asking_price / 100;
                    if self.requires_repair == 'yes':
                        table[year]['gross_rental_yield'] = self.gross_rental_yield * self.value_after_repair / 100;
                elif self.gross_rental_yield_unit == 'usd' or self.gross_rental_yield_unit == 'aed':
                    table[year]['gross_rental_yield'] = self.gross_rental_yield

            else:
                table[year]['gross_rental_yield'] = table[year-1]['gross_rental_yield']*(1+avg_annual_increase_percentage/100)

            #OPEX(Y)
            table[year]['OPEX']  = None
            if self.annual_op_expenses_unit == 'percent':
                table[year]['OPEX'] = self.annual_op_expenses * table[year]['gross_rental_yield'] / 100
            elif self.annual_op_expenses_unit == 'usd' or self.annual_op_expenses_unit == 'aed':
                table[year]['OPEX'] = self.annual_op_expenses
        
            #Annual Payment plan
            table[year]['AP']  = None
            #AP(Y) = A * sum(Xi * Ni) 
            # (for i iterating through periods that are partially or fully part of Y) and Ni = number of months of period i in Y
            if self.financing_option == FinancingOption.PAYMENT_PLAN:
                for i in range(start_i,len(self.instalment_plans)):
                    if total_instalment_duration>(year-1)*12: #if there is a residual
                        ni = total_instalment_duration - (year-1)*12
                        sum_instalment_percentage += (self.instalment_plans[i].percentage * ni)
                    else :
                        if total_instalment_duration + self.instalment_plans[i].duration < year*12:
                            total_instalment_duration+=self.instalment_plans[i].duration
                            sum_instalment_percentage += (self.instalment_plans[i].percentage * self.instalment_plans[i].duration)
                        elif total_instalment_duration + self.instalment_plans[i].duration == year*12:
                            total_instalment_duration+=self.instalment_plans[i].duration
                            sum_instalment_percentage += (self.instalment_plans[i].percentage * self.instalment_plans[i].duration)
                            start_i = i+1
                            break
                        else:
                            ni = year*12 - total_instalment_duration
                            total_instalment_duration+=self.instalment_plans[i].duration
                            sum_instalment_percentage += self.instalment_plans[i].percentage * ni
                            start_i = i
                            break
                if self.settlement_on_handover == True and ((year == self.settlement_duration/12 +1 and self.settlement_duration%12 != 0) 
                                                            or (year == self.settlement_duration/12 and self.settlement_duration%12 == 0)):
                    sum_instalment_percentage += self.settlement_percentage
                if self.post_handover == True:
                    total_duration = sum(plan.duration for plan in self.instalment_plans)
                    if year>total_duration/12 and year <= (total_duration+self.post_handover_duration)/12:
                        sum_instalment_percentage += self.post_handover_percentage
                table[year]['AP'] = self.asking_price * sum_instalment_percentage/100
                if year == 1:
                    table[year]['cumulative_AP'] = table[year]['AP']
                else:
                    table[year]['cumulative_AP'] = table[year-1]['cumulative_AP'] + table[year]['AP']

            #Expenses(Y)
            table[year]['Expenses'] = table[year]['OPEX']
            if year == 1:
                table[year]['Expenses'] += OTF_currency 
                if REP is not None:
                    table[year]['Expenses'] += REP
                if self.financing_option == FinancingOption.MORTGAGE or self.financing_option == FinancingOption.PAYMENT_PLAN:
                    table[year]['Expenses'] += downpayment_currency
            if self.financing_option == FinancingOption.MORTGAGE:
                table[year]['Expenses'] += yearly_mortgage_payment
            elif self.financing_option == FinancingOption.PAYMENT_PLAN:
                table[year]['Expenses'] += table[year]['AP']

            #property market value V(Y)
            table[year]['V'] = table[year-1]['V'] * (1 + CA/100)

            #cashflow CF(Y)
            table[year]['CF'] = table[year]['gross_rental_yield'] - table[year]['Expenses']

            if self.financing_option == FinancingOption.MORTGAGE:
                total_cash_invested = downpayment_currency + monthly_mortgage_payment * 12 * year
            elif self.financing_option == FinancingOption.PAYMENT_PLAN:
                total_cash_invested = downpayment_currency + table[year]['cumulative_AP']
            else:
                total_cash_invested = self.asking_price
            total_cash_invested += REP + OTF_currency

            #Cash on Cash return
            table[year]['CoC'] = table[year]['CF'] / total_cash_invested * 100

            #Cumulative cashflow
            if year == 1:
                table[year]['Cumulative_CF'] = table[year]['CF']
            else:
                table[year]['Cumulative_CF'] = table[year]['CF'] + table[year-1]['Cumulative_CF']

            #Return on investment
            table[year]['ROI'] = table[year]['Cumulative_CF'] + CA/100 * table[year-1]['V']/total_cash_invested*100

            if self.financing_option == FinancingOption.MORTGAGE:
                table[year]['OM'] = monthly_mortgage_payment * 12 * (mortgage_length_in_years - year)
                #Equity in currency
                table[year]['Equity_currency'] = table[year]['V'] - table[year]['OM']
                #Equity in percentage
                table[year]['Equity_percent'] = (table[year]['V'] - table[year]['OM'])/table[year]['V']*100
            elif self.financing_option == FinancingOption.PAYMENT_PLAN:
                table[year]['Equity_currency'] = self.asking_price - downpayment_currency - table[year]['cumulative_AP']
            else:
                table[year]['Equity_currency'] = table[year]['V']
            #Return on equity
            table[year]['ROE'] = table[year]['CF'] / table[year]['Equity_currency'] * 100

        print("table")
        del table[0]

        table = customize(table)
        print("table")
        print(table)
        return table

def customize(table):
    # Remove keys having None values
    result = {}
    for year, data in table.items():
        # Create a new dictionary for this year, excluding None values
        result[year] = {k: v for k, v in data.items() if v is not None}
    table = result
    
    #remove total_cash_invested for all years
    for year in table:
        if 'total_cash_invested' in table[year]:
            del table[year]['total_cash_invested']
        if 'cumulative_AP' in table[year]:
            del table[year]['cumulative_AP']

    # Define key mappings
    key_mappings = {
        'OPEX': 'Operating Expenses',
        'AP': 'Annual Payment Plan',
        'V': 'Property Market Value',
        'CF': 'Cashflow',
        'CoC': 'Cash on Cash return',
        'Cumulative_CF': 'Cumulative Cashflow',
        'cumulative_AP': 'Cumulative Annual Payment Plan',
        'ROI': 'Return on Investment',
        'OM': 'Outstanding Mortgage',
        'Equity_currency': 'Equity in currency',
        'Equity_percent': 'Equity in percentage',
        'ROE': 'Return on Equity',
        'total_cash_invested': 'Total Cash Invested',
        'Expenses': 'Total Expenses',
        'gross_rental_yield': 'Gross Rental Yield'
    }
    
    # Rename keys in the table
    for year in table:
        table[year] = {key_mappings.get(k, k): v for k, v in table[year].items()}
    
    #sanity check : ensure all keys are the same for all years
    for year in table:
        if table[year].keys() != table[1].keys():
            print(f"Keys in year {year} do not match keys in year 1")
            print(f"Keys in year {year}: {table[year].keys()}")
            print(f"Keys in year 1: {table[1].keys()}")
            raise ValueError("Keys in year 1 do not match keys in other years")
    return table


class CashflowCalcForm(FlaskForm):
    currency = SelectField('Currency', choices=[(c.value, c.value) for c in Currency], validators=[DataRequired()])
    project_name = StringField('Project Name:', validators=[DataRequired()])
    property_usage = StringField('Property Usage:', validators=[DataRequired()])
    property_type = StringField('Property Type:', validators=[DataRequired()])
    property_sub_type = StringField('Property Subtype:', validators=[DataRequired()])
    property_area = FloatField('Total Property Area:', validators=[DataRequired()])
    area_unit = SelectField('Area Unit', choices=[('sqm', 'm²'), ('sqft', 'sqft')], validators=[DataRequired()])
    asking_price = FloatField('Asking Price', validators=[DataRequired()])
    #requires_repair = SelectField('Does the property require repair?', choices=[('yes', 'Yes'), ('no', 'No')], validators=[DataRequired()])
    requires_repair = SelectField(
        'Does the property require repair?',
        choices=[('', 'Select an option'), ('yes', 'Yes'), ('no', 'No')],
        validators=[DataRequired(message="Please select either 'Yes' or 'No'.")],
        coerce=str
    )
    repair_fees = FloatField('Repair Fees', validators=[Optional()])
    value_after_repair = FloatField('Value After Repair', validators=[Optional()])
    gross_rental_yield = FloatField('Annual Gross Rental Yield:', validators=[DataRequired()])
    #gross_rental_yield_unit = SelectField('Gross Rental Yield Unit', choices=[('percent', '%'), ('usd', 'USD'), ('aed', 'AED')], validators=[DataRequired()])
    gross_rental_yield_unit = SelectField('Gross Rental Yield Unit', choices=[('percent', '%'), ('currency', '')], validators=[DataRequired()])
    
    annual_increase = FloatField('Average Annual Increase of Property Gross Rental Yield (%):', validators=[DataRequired()])
    annual_op_expenses = FloatField('Annual operating expenses:', validators=[DataRequired()])
    annual_op_expenses_unit = SelectField('Annual Operating Expenses Unit', choices=[('percent', '% of gross rental yield'),('currency', '')], validators=[DataRequired()])
    onetime_acq_fee = FloatField('One-time acquisition fees (taxes, brokers fees, notary fees):', validators=[DataRequired()])
    fee_unit = SelectField('Fee Unit', choices=[('percent', '% of the asking price'), ('currency', '')], validators=[DataRequired()])
    financing_option = RadioField(
        'Financing Option',
        choices=[
            (FinancingOption.MORTGAGE.value, 'Mortgage'),
            (FinancingOption.PAYMENT_PLAN.value, 'Payment Plan'),
            (FinancingOption.NONE.value, 'None')
        ],
        validators=[DataRequired()]
    )
    #these fields are only relevant if the financing option is mortgage
    mortgage_annual_ir = FloatField('Mortgage Annual Interest Rate:', validators=[Optional()])
    mortgage_downpayment = FloatField('Mortgage Downpayment:', validators=[Optional()])
    mortgage_downpayment_unit = SelectField('Mortgage Downpayment Unit', choices=[('percent', '% of the asking price'), ('currency', '')], validators=[Optional()])
    mortgage_length = IntegerField('How long is your mortgage for?', validators=[Optional()])
    mortgage_length_unit = SelectField('Mortgage Length Unit', choices=[('months', 'Months'), ('years', 'Years')], validators=[Optional()])
    
    #these fields are only relevant if the financing option is payment plan
    plan_downpayment = FloatField('Downpayment:', validators=[Optional()])
    plan_downpayment_unit = SelectField('Plan Downpayment Unit', choices=[('percent', '% of the asking price'), ('currency', '')], validators=[Optional()])
    instalment_plans = FieldList(FormField(InstalmentPlanForm), min_entries=1)
    
    settlement_on_handover = BooleanField('Settlement On Handover')
    settlement_percentage = FloatField('In Percentage of asking price:', validators=[Optional()])
    settlement_duration = IntegerField('Handover date (Number of months after the acquisition date/first payment):', validators=[Optional()])
    post_handover = BooleanField('Post Handover Payment Plan')
    post_handover_percentage = FloatField('In Percentage of asking price:', validators=[Optional()])
    post_handover_duration = IntegerField('Number of months after handover:', validators=[Optional()])
    cashflow_analysis_period = IntegerField('For how many years do you want the cashflow analysis?', validators=[DataRequired()])
    annual_capital_appreciation = FloatField('Expected Annual Capital Appreciation (%):', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(CashflowCalcForm, self).__init__(*args, **kwargs)
        self.instalment_plans.validators = [Optional()]


    def create_object(self):
        instalment_plans = [
            plan.create_object()
            for plan in self.instalment_plans
            if plan.percentage.data is not None and plan.duration.data is not None
        ] if self.financing_option.data == FinancingOption.PAYMENT_PLAN.value else None

        return Property(
            self.project_name.data,
            self.property_usage.data,
            self.property_type.data,
            self.property_sub_type.data,
            self.property_area.data,
            self.area_unit.data,
            self.asking_price.data,
            self.requires_repair.data,
            self.repair_fees.data,
            self.value_after_repair.data,
            self.gross_rental_yield.data,
            self.gross_rental_yield_unit.data,
            self.annual_increase.data,
            self.annual_op_expenses.data,
            self.annual_op_expenses_unit.data,
            self.onetime_acq_fee.data,
            self.fee_unit.data,
            FinancingOption(self.financing_option.data),
            mortgage_annual_ir=self.mortgage_annual_ir.data,
            mortgage_downpayment=self.mortgage_downpayment.data,
            mortgage_downpayment_unit=self.mortgage_downpayment_unit.data,
            mortgage_length=self.mortgage_length.data,
            mortgage_length_unit=self.mortgage_length_unit.data,
            plan_downpayment=self.plan_downpayment.data,
            plan_downpayment_unit=self.plan_downpayment_unit.data,
            instalment_plans=instalment_plans,
            settlement_on_handover=self.settlement_on_handover.data,
            settlement_percentage=self.settlement_percentage.data,
            settlement_duration=self.settlement_duration.data,
            post_handover=self.post_handover.data,
            post_handover_percentage=self.post_handover_percentage.data,
            post_handover_duration=self.post_handover_duration.data,
            cashflow_analysis_period=self.cashflow_analysis_period.data,
            annual_capital_appreciation=self.annual_capital_appreciation.data
        )

    
