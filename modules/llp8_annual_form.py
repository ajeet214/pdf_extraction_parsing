from wand.image import Image
from PIL import Image as PI
import pyocr
import pyocr.builders
import io
import re
import os
import json


class Lllp8Annual:

    def __init__(self, path):
        # print(pyocr.get_available_tools())
        tool = pyocr.get_available_tools()[0]
        lang = tool.get_available_languages()[tool.get_available_languages().index('eng')]

        # print(lang)

        req_image = list()
        self.final_text = list()

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
        f_dict = dict()
        # print(final_text[0].split('\n'))
        page1 = self.final_text[0]
        # print(page1)

        doc_type = re.search('Annual or Interim (.*)\n', page1).group(1)
        if doc_type[doc_type.index('Annual') - 2] == '0' or doc_type[doc_type.index('Annual') - 2] == 'O':
            f_dict['fileType'] = 'LLP-8 Interim'
        else:
            f_dict['fileType'] = 'LLP-8 Annual'

        # Limited Liability Partnership identification number
        LLPIN = re.search('/ Foreign Limited Liability Partnership (.*)\n', page1).group(1).split()[0]
        f_dict['lLPIN'] = LLPIN.replace('_', '-')

        # Statement of Account and Solvency
        statement_of_acc_sol = re.search('Statement of Account and Solvency as at: (.*)\n', page1).group(1)[
                               :-1].replace(' ', '')
        f_dict['year'] = re.search('\d+', statement_of_acc_sol.split('/')[-1]).group()
        f_dict['statementdate'] = statement_of_acc_sol

        # parsing of name of LLP
        lLPINname = re.search('Name of Limited Liability(.*\n)+Partnership\(FLLP\)', page1).group(0). \
            replace('Name of Limited Liability\n', '').replace('Partnership(LLP)/\n', ''). \
            replace('Foreign Limited Liability\n', '').replace('Partnership(FLLP)', '')

        if lLPINname.startswith('\n'):
            f_dict['lLPINname'] = ''
        else:
            f_dict['lLPINname'] = lLPINname

        # extraction of LLP email-id
        llp_email_id = re.search('e-mail ID of the LLP (.*)\n', page1).group(1)

        # Total monetary value of obligation of contribution as on above date (in Rs.)
        temp1 = page1.index('Total monetary value of obligation of contribution as on above date')
        temp2 = page1.index('Part A: Statement of Solvency')
        try:
            total_monetary_value = int(page1[temp1:temp2].split()[-1])
        except ValueError:
            total_monetary_value = ''
        # Address of registered office of the LLP or principal place of business in India of the FLLP
        temp3 = page1.index('Partnership(FLLP)')
        temp4 = page1.index('*e-mail ID of the LLP')

        try:
            address_of_registered_office = page1[temp3:temp4].replace('principa| place of business', ''). \
                replace('in India Of the FLLP', '').replace('office of the LLP or', '')

            llp_office_address = " ".join(
                address_of_registered_office[re.search('registered', address_of_registered_office).end():].split())
        except AttributeError:
            address_of_registered_office = page1[temp3:temp4].replace('In lndla Of the FLLP', ''). \
                replace('Oﬁlce of the LLP or', '').replace('principal place of business ', '')

            llp_office_address = " ".join(
                address_of_registered_office[re.search('’egiSte’ed', address_of_registered_office).end():].split())

        # address_of_registered_office = final_text[0][temp3:temp4]
        # print(address_of_registered_office)

        f_dict['address'] = llp_office_address.replace('principal place of business', ''). \
            replace('in India of the FLLP', '')
        f_dict['lLPINemailid'] = llp_email_id
        f_dict['valueofobligationofcontribution'] = total_monetary_value

        # print(f_dict)
        ####-----------------------page 2 ---------------------

        dict_2 = dict()
        page_2 = self.final_text[1]
        # print(page_2)

        dict_2['contributionReceived'] = \
        re.search('(.*)\n(.*)\n2.Liabilities', page_2).group(1).split('\n')[0].split(' ')[0]
        dict_2['reserves&Surplus'] = re.search('(.*)\n(.*)\n2.Liabilities', page_2).group().split('\n')[1].split(' ')[
            -2]
        dict_2['securedLoans'] = re.search('Secured loans (.*)\n', page_2).group(1).split(' ')[0]
        dict_2['unsecuredLoans'] = re.search('Unsecured loans (.*)\n', page_2).group(1).split(' ')[0]
        dict_2['shortTermBorrowing'] = re.search('Short term borrowing (.*)\n', page_2).group(1).split(' ')[0]
        dict_2['creditors/tradePayables'] = re.search('Creditors/trade payables - (.*)\n', page_2).group(1).split(' ')[
            0]
        dict_2['otherLiabilitiesCurrentLiabilities'] = \
        re.search('Other liabilities \(to specify\) (.*)\n', page_2).group(1).split(' ')[0]

        try:
            dict_2['forTaxation'] = re.search('for taxation (.*)\n', page_2).group(1).split(' ')[0]
        except AttributeError:
            dict_2['forTaxation'] = ''

        dict_2['forContingencies'] = re.search('for contingencies (.*)\n', page_2).group(1).split(' ')[0]
        dict_2['forInsurance'] = re.search('for insurance (.*)\n', page_2).group(1).split(' ')[0]
        dict_2['otherProvisions'] = re.search('Other provisions \(if any\) (.*)\n', page_2).group(1).split(' ')[0]

        try:
            dict_2['totalContributionAndLiabilities'] = re.search('Total (.*)\n', page_2).group(1).split(' ')[0]
        except AttributeError:
            dict_2['totalContributionAndLiabilities'] = re.search('TOtal (.*)\n', page_2).group(1).split(' ')[0]

        dict_2['grossFixedAssets'] = \
        re.search('(.*)\nLess: depreciation and amortization (.*)\n', page_2).group(1).split()[-2]
        dict_2['lessDepreciationAndAmortization'] = \
        re.search('Less: depreciation and amortization (.*)\n', page_2).group(1).split(' ')[0]
        dict_2['netFixedAssets'] = re.search('Net fixed assets (.*)\n', page_2).group(1).split(' ')[0]

        try:
            dict_2['investments'] = re.search('Investments (.*)\n', page_2).group(1).split(' ')[0]
        except AttributeError:
            dict_2['investments'] = re.search('Net fixed assets (.*)\n(.*)', page_2).group().split('\n')[1].split(' ')[
                1]

        try:
            dict_2['loansAndAdvances'] = re.search('Loans and advances (.*)\n', page_2).group(1).split(' ')[0]
        except AttributeError:
            dict_2['loansAndAdvances'] = ""

        dict_2['inventories'] = re.search('Inventories (.*)\n', page_2).group(1).split(' ')[0]
        dict_2['debtors/tradeReceivables'] = re.search('Debtors/trade receivables (.*)\n', page_2).group(1).split(' ')[
            0]
        dict_2['cashAndCashEquivalents'] = re.search('Cash and cash equivalents (.*)\n', page_2).group(1).split(' ')[-2]
        dict_2['otherAssets'] = re.search('Other assets (.*)\n', page_2).group(1).split(' ')[0]
        dict_2['totalAssets'] = re.search('TOTAL (.*)\n', page_2).group(1).split(' ')[0]

        f_dict['statementOfAssetsAndLiabilities'] = dict_2

        # print(f_dict)
        ### -----------------------page 3-----------------------
        page_3 = self.final_text[2]
        # print(page_3)
        dict_3 = dict()
        list_of_all_content = re.search('From(.*\n)+\d(.*)\n', page_3).group().split('\n')

        dict_3['grossTurnover'] = list_of_all_content[2].split(' ')[0]
        dict_3['lessExciseDutyOrServiceTax'] = list_of_all_content[3].split(' ')[0]
        dict_3['domesticsaleOfGoodsManufactured'] = list_of_all_content[4].split(' ')[0]
        dict_3['domesticsaleOfGoodsTraded'] = list_of_all_content[5].split(' ')[0]
        dict_3['domesticsaleOrSupplyOfServices'] = list_of_all_content[6].split(' ')[0]
        dict_3['exportSaleOfGoodsManufactured'] = list_of_all_content[7].split(' ')[0]
        dict_3['exportSaleOfGoodsTraded'] = list_of_all_content[8].split(' ')[0]
        dict_3['exportSaleOrSupplyOfServices'] = list_of_all_content[9].split(' ')[0]
        dict_3['otherIncome'] = list_of_all_content[10].split(' ')[0]
        dict_3['increaseDecreaseInStocks'] = list_of_all_content[11].split(' ')[0]
        dict_3['totalIncome'] = list_of_all_content[12].split(' ')[0]
        dict_3['rawMaterialConsumed'] = list_of_all_content[13].split(' ')[0]
        dict_3['purchasesMadeForReSale'] = list_of_all_content[14].split(' ')[0]
        dict_3['consumptionOfStoresAndSpareParts'] = list_of_all_content[15].split(' ')[0]
        dict_3['powerAndFuel'] = list_of_all_content[16].split(' ')[0]
        dict_3['personnelExpenses'] = list_of_all_content[17].split(' ')[0]
        dict_3['administrativeExpenses'] = list_of_all_content[18].split(' ')[0]
        dict_3['paymentToAuditors'] = list_of_all_content[19].split(' ')[0]
        dict_3['sellingExpenses'] = list_of_all_content[20].split(' ')[0]
        dict_3['insuranceExpenses'] = list_of_all_content[21].split(' ')[0]

        dict_3['depreciationAndAmortization'] = list_of_all_content[22].split(' ')[0]
        dict_3['interest'] = list_of_all_content[23].split(' ')[0]
        dict_3['otherExpenses'] = list_of_all_content[24].split(' ')[0]
        dict_3['totalExpenditure'] = list_of_all_content[25].split(' ')[0]
        dict_3['netProfitOrNetLoss'] = list_of_all_content[26].split(' ')[0]
        dict_3['provisionForTax'] = list_of_all_content[27].split(' ')[0]
        dict_3['profitAfterTax'] = list_of_all_content[28].split(' ')[0]
        dict_3['profitTransferredToPartnersAccount'] = list_of_all_content[29].split(' ')[0]
        dict_3['profitTransferredToReservesAndSurplus'] = list_of_all_content[30].split(' ')[0]

        f_dict['statementOfIncomeAndExpenditure'] = dict_3

        # print(f_dict)
        # ### ---------------------page 4 ------------------------
        page_4 = self.final_text[3]
        # print(page_4)
        certificate_by = re.search('Certificate by (.*)\n', page_4).group(1).split(' or ')
        # print(certificate_by)
        for i in certificate_by:
            if i.startswith('G'):
                f_dict['CertificateBy'] = i.split()[1]

        # membershipNumber = re.search('DPIN/ Income-tax PAN/ Membership number (.*)\n', page_4).group(1).split()[0]
        # f_dict['dPIN/Income-taxPAN/MembershipNumber'] = membershipNumber
        f_dict['nameDesignatedPartne/AuthorizedRepresentative/Auditor'] = ''

        try:
            address_line_1 = re.search('Address (.*)\n', page_4).group(1).replace('*Line I ', '')
        except AttributeError:
            address_line_1 = re.search('Add(.*)\n', page_4).group().replace('*Line I ', ''). \
                replace('*Line | ', '').replace('*Add’ess ', '')
        try:
            city = re.search('City (.*)District', page_4).group(1).replace('*', '')
        except AttributeError:
            city = re.search('City (.*)Dist', page_4).group(1).replace('*', '')

        try:
            district = re.search('District (.*)\n', page_4).group(1)
        except AttributeError:
            district = re.search('Dist(.*)\n', page_4).group(1)

        state_pin = re.search('State (.*)\n', page_4).group(1).split('Pin code ')
        country = re.search('Country (.*)\n', page_4).group(1)
        state = state_pin[0]
        pin_code = state_pin[1].split()[-1]

        try:
            address_line_2 = re.search('Line \|\|(\n+.*)+City', page_4).group().replace('*City', ''). \
                replace('\n', '').replace('         ', '*').split('*')[1].strip()
        except AttributeError:
            address_line_2 = re.search('Line (.*)\n(.*)City', page_4).group().replace('*City', ''). \
                replace('\n', '')

        # print(address_line_2)
        f_dict['addressAttachment'] = '{} {} {} {} {} {} {}'.format(address_line_1,
                                                                    address_line_2,
                                                                    city, district,
                                                                    state,
                                                                    pin_code,
                                                                    country)

        try:
            f_dict['emailIdAttachment'] = re.search('e-mail(.*)\n\w+@\w+\.\w+', page_4).group().split('\n')[1]
        except AttributeError:
            f_dict['emailIdAttachment'] = re.search('[\w.\]]+@(\w)+\.\w+(\.\w+)?', page_4).group().replace('\n', '')

        # print(list(filter(None, re.search('[\w.\]]+@(\w)+\.\w+(\.\w+)?\n+(.*\n)+Pre', page_4).group().split('\n')[1:-1])))
        # print(re.sub(' {2,}', ' ', re.search('[\w.\]]+@(\w)+\.\w+(\.\w+)?\n+(.*\n)+Pre', page_4).group()))

        return f_dict


if __name__ == '__main__':
    Obj = Lllp8Annual('../data/LLP Form8-06112019_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-31102019_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-02112018_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-24102016_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-19012019_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-01122017_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-15112018_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-04012018_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-26102016_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-26102019_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-30102017_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-30102018_signed.pdf')
    # Obj = Lllp8Annual('../data/LLP Form8-31102017_signed.pdf')
    print(Obj.data_parsing())

