from wand.image import Image
from PIL import Image as PI
import pyocr
import pyocr.builders
import io
import re
import os
import json


class Lllp8Interim:
    
    def __init__(self, path):
        tool = pyocr.get_available_tools()[0]
        lang = tool.get_available_languages()[2]
        
        print(lang)
        req_image = []
        self.final_text = []
        
        image_pdf = Image(filename=path, resolution=300)
        image_jpeg = image_pdf.convert('jpeg')
        
        for img in image_jpeg.sequence:
            img_page = Image(image=img)
            req_image.append(img_page.make_blob('jpeg'))
        
        print(len(req_image))
        for img in req_image:
            txt = tool.image_to_string(
                PI.open(io.BytesIO(img)),
                lang=lang,
                builder=pyocr.builders.TextBuilder()
            )
            self.final_text.append(txt)
    
    def data_parsing(self):
        # print('\n'.join(final_text))
        f_dict = dict()
        
        # ----------------------------------------page 1 -----------------------------------
        page1 = self.final_text[0]
        # print(page1)
        
        doc_type = re.search('Annual or Interim (.*)\n', page1).group(1)
        if doc_type.startswith('6'):
            f_dict['fileType'] = 'LLP-8 Annual'
        else:
            f_dict['fileType'] = 'LLP-8 Interim'
        
        # 1.
        llpin = re.search('Limited Liability Partnership identification number (.*)\n', page1).group(1).split('or')[1].strip()
        f_dict['lLPIN'] = llpin.replace('_', '-')
        
        # 2(a).
        name_llp = re.search('Name of the LLP/ FLLP (.*)\n', page1).group(1)
        f_dict['lLPINname'] = name_llp
        
        option_2 = re.search('2\.(.*\n)+3\.', page1).group().split('\n')
        # print(option_2)

        # 2(b).
        address = ' '.join(re.search('2. \(a\)(.*\n)+3. \(a\)', page1).group().split('\n')[1:-2])
        f_dict['address'] = address.replace('prInCIple place of ', '').replace('business in India of ', '').\
                            replace('the FLLP ', '').replace('° .\'°": ° t e 0\'', '').\
                            replace('(\'0) Agfj’esii 0,: ’eLgLisF’fe’ed ', '')
        # 2(c).
        llpin_emailid = option_2[-2].split(' ')[-1]
        f_dict['lLPINemailid'] = llpin_emailid
        
        
        # 3(a)
        this_form_is_for = re.search('This form is for (.*)\n', page1).group()
        # print(this_form_is_for)
        if this_form_is_for[this_form_is_for.index('Creation')-1] == '@':
            f_dict['thisFormIsFor'] = 'Creation of charge'
        elif this_form_is_for[this_form_is_for.index('Modification')-1] == '@':
            f_dict['thisFormIsFor'] = 'Modification of charge'
        else:
            f_dict['thisFormIsFor'] = 'Satisfaction of charge'
        
        
        # 3(b)
        charge_iden_no = re.search('Charge identification number (.*)\n', page1).group(0).split(' ')[-1].replace('\n', '')
        # print(charge_iden_no)
        f_dict['chargeIdentificationNumber'] = charge_iden_no
        
        # 3(c)
        temp1 = re.search('Whether charge is modified in favour of asset reconstruction company \(ARC\) or assignee (.*)\n', page1).group(0).split(' ')
        # print(temp1)
        if temp1[-1].startswith('@'):
            f_dict['whetherChargeIsModifiedInFavorOfARCOrAssignee'] = 'No'
        else:
            f_dict['whetherChargeIsModifiedInFavorOfARCOrAssignee'] = 'Yes'
        
        # 4
        list_of_charge = list()
        type_of_charge = re.search('4-(.*\n){3}', page1).group()
        # print(type_of_charge)
        if type_of_charge.find('.1 Immoveable property') != -1:
            list_of_charge.append('Immoveable property')
        if type_of_charge.find('.1 Ship') != -1:
            list_of_charge.append('Ship')
        if type_of_charge.find('.1 Any interest in immoveable property') != -1:
            list_of_charge.append('Any interest in immoveable property')
        if type_of_charge.find('.1 Goodwill') != -1:
            list_of_charge.append('Goodwill')
        if type_of_charge.find('.1 Book debts') != -1:
            list_of_charge.append('Book debts')
        if type_of_charge.find('.1 Trade marks') != -1:
            list_of_charge.append('Trade marks')
        if type_of_charge.find('.1 Patent, licence under a patent') != -1:
            list_of_charge.append('Patent, licence under a patent')
        if type_of_charge.find('.1 Floating charge') != -1:
            list_of_charge.append('Floating charge')
        if type_of_charge.find('.1 Moveable property (not being pledge)') != -1:
            list_of_charge.append('Moveable property (not being pledge)')
        if type_of_charge.find('.1 Copyright or licence under copy right') != -1:
            list_of_charge.append('Copyright or licence under copy right')
        f_dict['typeOfCharge'] = ', '.join(list_of_charge)
        # 5(a)
        consortium_finance = re.search('Whether consortium finance is involved (.*)\n', page1).group(1)
        # print(consortium_finance)
        if consortium_finance.startswith('0') or consortium_finance.startswith('O'):
            f_dict['whetherConsortiumFinanceIsInvolved'] = 'No'
        else:
            f_dict['whetherConsortiumFinanceIsInvolved'] = 'Yes'
        
        # 5(b)
        joint_charge = re.search('whether joint charge is involved (.*)6', page1).group(1)
        # print(joint_charge)
        if joint_charge.startswith('0') or joint_charge.startswith('O'):
            f_dict['whetherJointChargeIsInvolved'] = 'No'
        else:
            f_dict['whetherJointChargeIsInvolved'] = 'Yes'
        
        # 6
        charge_holders = re.search('Number of charge holders (.*)\n', page1).group(1)
        # print(charge_holders)
        f_dict['numberOfChargeHolders'] = charge_holders
        
        # 7. Particulars of charge holders------------------------------
        charge_holder_dict = dict()
        charge_holder_cat = re.search('Category (.*)\n', page1).group(1)
        # print(charge_holder_cat)
        charge_holder_dict['category'] = charge_holder_cat
        charge_holder_name = re.search('Name\n\n(.*)\n\*A', page1).group(1)
        # print(charge_holder_name)
        charge_holder_dict['nameOfChargeHolder'] = charge_holder_name
        
        address_line_1 = re.search('ddress(.*\n)+Line (.*\n)+(.*)City', page1).group(0).split('Line')[0].\
                          replace('\n', '').replace('ddress Um I ', '')
        # print(address_line_1)
        address_line2 = ' '.join(re.search('Line (.*\n)+(.*)City', page1).group().split('\n')[1:-1])
        # print(address_line2)
        city = re.search('City (.*)District', page1).group(1).replace('*', '')
        district = re.search('District (.*)\n', page1).group(1)
        state_pin = re.search('State (.*)\n', page1).group(1).split('*')
        country = re.search('Country (.*)\n', page1).group(1)
        state = state_pin[0]
        pin_code = state_pin[1].split()[-1]
        # print(city)
        # print(district)
        # print(state)
        # print(pin_code)
        # print(country)
        
        address = '{} {} {} {} {} {} {}'.format(address_line_1, address_line2, city, district, state, pin_code, country)
        charge_holder_dict['addressParticularsOfChargeHolder'] = address
        
        particulars_phone_email = re.search('Phone(.*\n)+', page1).group()
        particulars_email = re.search('e-mail (.*)\n', particulars_phone_email).group().split(' ')[-1].replace('\n', '')
        # print(particulars_email)
        particulars_phone = re.search('Phone(.*)Fax', particulars_phone_email).group(1)
        # print(particulars_phone)
        charge_holder_dict['phoneParticularsOfChargeHolder'] = particulars_phone
        charge_holder_dict['emailIdParticularsOfChargeHolder'] = particulars_email
        
        f_dict['particularsOfChargeHolder'] = [charge_holder_dict]
        # ---------------------------------------page 2----------------------------------------
        page2 = self.final_text[1]
        # print(page2)
        
        # 8
        nature_or_des = re.search('Nature or description of instrument(.*\n\n)+', page2).group().split('\n')[4]
        # print(nature_or_des)
        f_dict['natureOrDescriptionOfInstrument'] = nature_or_des
        
        # 9(a)
        instrument_creation_date = re.search('Date of the instrument creating the charge (.*)\n', page2).group(1).split(' ')[0]
        # print(instrument_creation_date)
        f_dict['dateOfTheInstrumentCreatingTheCharge'] = instrument_creation_date
        
        # 9(b)
        instrument_mod_date = re.search('Date of the instrument modifying the charge (.*)\n', page2).group(1).split(' ')[0]
        # print(instrument_mod_date)
        f_dict['dateOfTheInstrumentModifyingTheCharge'] = instrument_mod_date
        
        # 10(a)
        instrument_created_or_modified = re.search('Whether charge created or modified outside India (.*)\n', page2).group(1)
        # print(instrument_created_or_modified)
        if instrument_created_or_modified.startswith('0') or instrument_created_or_modified.startswith('O'):
            f_dict['whetherChargeCreatedOrModifiedOutsideIndia'] = 'No'
        else:
            f_dict['whetherChargeCreatedOrModifiedOutsideIndia'] = 'Yes'
        
        # 11(a)
        amount_secured = re.search('Amount secured by the charge in words(.*\n)+\(c\) In', page2).group()
        amount_secured = re.search('\d+', amount_secured).group()
        # print(amount_secured)
        f_dict['amountSecuredByTheCharge'] = amount_secured
        
        # 12(a)
        rate_of_interest = re.search('Rate of Interest (.*)\n', page2).group(1)
        # print(rate_of_interest)
        f_dict['rateOfInterest'] = rate_of_interest
        
        # 12(b)
        terms_of_repayment = re.search('Terms of repayment (.*)\n', page2).group(1)
        # print(terms_of_repayment)
        f_dict['termsOfRepayment'] = terms_of_repayment
        
        # 12(c)
        margin = re.search('(.*)\n(.*)Margin(.*)\n', page2).group().replace('(c)', '').replace(' Margin ', '')
        margin = re.search('[a-zA-Z0-9]+(.*)\n(.*)', margin).group().replace('\n', ' ')
        # print(margin)
        f_dict['margin'] = margin
        
        # 12(d)
        extent_operation = re.search('(.*)\n(.*)Extent and operation of the charge(.*)\n(.*)', page2).group().replace('(d)', '').replace(' *Extent and operation of the charge ', '')
        extent_operation = re.search('[a-zA-Z0-9]+(.*)\n(.*)\n(.*)', extent_operation).group().replace('\n', ' ')
        # print(extent_operation)
        f_dict['extentAndOperationOfTheCharge'] = extent_operation
        
        # 14
        short_particulars = re.search('Short particulars Of the property (.*)\n(.*)\n(.*)', page2).group()\
                            .replace('Short particulars Of the property ', '')\
                            .replace('charged (including location Of the ', '').replace('property) ', '').replace('\n', ' ')
        # print(short_particulars)
        f_dict['shortParticularsOfThePropertyCharged'] = short_particulars
        
        # ---------------------------------------page 3----------------------------------------
        page3 = self.final_text[2]
        # print(page3)
        
        # 15(a)
        property_reg_llp = re.search('Whether any of the property or interest therein under reference is not registered in the name of the LLP (.*)\n', page3).group(1)
        # print(property_reg_llp)
        if property_reg_llp.startswith('0') or property_reg_llp.startswith('O'):
            f_dict['whetherAnyThePropertyOrInterestRegisteredInTheNameOfTheLLP'] = 'No'
        else:
            f_dict['whetherAnyThePropertyOrInterestRegisteredInTheNameOfTheLLP'] = 'Yes'
        
        # 15(b)
        try:
            reg_name = re.search('If yes, in whose name it is registered (.*)\n', page3).group(1)
            f_dict['ifYesInWhoseNameItIsRegistered'] = reg_name
        except AttributeError:
            f_dict['ifYesInWhoseNameItIsRegistered'] = ''
        
        # 16
        extent_operation = re.search('(.*)\n(.*)Partlculars of present modlflcatlon(.*)\n(.*)', page3).group().replace(' Partlculars of present modlflcatlon ', '').replace('16', '')
        extent_operation = re.search('[a-zA-Z0-9]+(.*)\n(.*)\n(.*)', extent_operation).group().replace('\n', ' ')
        # print(extent_operation)
        f_dict['particularsOfPresentModification'] = extent_operation
        
        # 17
        # print(page3)
        date_of_satisfaction = re.search('Date of satisfaction in full (.*)\n', page3).group(1).split(' ')[0]
        if date_of_satisfaction.startswith('(DD'):
            f_dict['dateOfSatisfactionInFull'] = ''
        else:
            f_dict['dateOfSatisfactionInFull'] = date_of_satisfaction
        # print(date_of_satisfaction)

        return f_dict
        

if __name__ == '__main__':

    Obj = Lllp8Interim("data/LLP Form8-13042017_signed.pdf")
    print(Obj.data_parsing())
