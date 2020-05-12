from wand.image import Image
from PIL import Image as PI
import pyocr
import json
import pyocr.builders
import io
import os
import PyPDF2
from collections import OrderedDict


class ChgOneForm:

    def __init__(self, path):
        tool = pyocr.get_available_tools()[0]
        lang = tool.get_available_languages()[1]

        self.path = path
        req_image = list()
        self.final_text = list()

        image_pdf = Image(filename=self.path, resolution=275)

        image_jpeg = image_pdf.convert("jpeg")

        for img in image_jpeg.sequence:
            img_page = Image(image=img)
            req_image.append(img_page.make_blob("jpeg"))

        for img in req_image:
            txt = tool.image_to_string(
                PI.open(io.BytesIO(img)), builder=pyocr.builders.TextBuilder()
            )
            self.final_text.append(txt)

    def check_substring(self, string, sub_string1):
        a = string.find(sub_string1)
        if a == -1:
            return a
        return a

    def extract_parse_createjson_frompdf(self):

        page_2_text = self.final_text[1]

        answer3 = list()
        send1 = dict()

        send_to_json = {
            "fileType": "CHG-1",
            "thisFormIsForRegistrationOf": None,
            "theApplicantIs": None,
            "whetherChargeIsModifiedInFavourOfARCOrAssignee": None,
            "whetherChargeIsCreatedOrModifiedOutsideIndia": None,
            "whetherConsortiumFinance": None,
            "whetherJointChargeIsInvolved": None,
            "whetherAnyOfTheIsNotRegisteredInTheNameOfTheCompany": None,
        }

        full_string = ""
        for i in range(len(self.final_text)):
            full_string += self.final_text[i]

        form_registration = full_string.rfind("This form is for registration of")
        if form_registration != -1:
            form_registration_substring = full_string[
                form_registration : form_registration + 85
            ]
            values = form_registration_substring.find("@")
            if values != -1:
                value = form_registration_substring[values : values + 15]
                if value.find("Creation") != -1:
                    send_to_json["thisFormIsForRegistrationOf"] = "Creation of charge"
                else:
                    send_to_json["thisFormIsForRegistrationOf"] = "Modification of charge"

        applicant = full_string.rfind("Whether the applicant is")
        if applicant != -1:
            applicant_substring = full_string[applicant : applicant + 65]
            values = applicant_substring.find("@")
            if values != -1:
                value = form_registration_substring[values: values + 15]
                if value.find("Company") != -1:
                    send_to_json["theApplicantIs"] = "The Company"
                else:
                    send_to_json["theApplicantIs"] = "The charge holder"

        arc = full_string.rfind(
            "Whether charge is modified in favour of asset reconstruction company (ARC) or assignee"
        )
        if arc != -1:
            arc_substring = full_string[arc : arc + 99]
            values = arc_substring.find("@")
            if values != -1:
                value = arc_substring[values : values + 4]
                if value.find("Y") != -1:
                    send_to_json["whetherChargeIsModifiedInFavourOfARCOrAssignee"] = "Yes"
                else:
                    send_to_json["whetherChargeIsModifiedInFavourOfARCOrAssignee"] = "No"

        india = full_string.rfind("Whether charge is created or modified outside India")
        if india != -1:
            india_substring = full_string[india : india + 66]
            values = india_substring.find("@")
            if values != -1:
                value = india_substring[values : values + 4]
                if value.find("Y") != -1:
                    send_to_json["whetherChargeIsCreatedOrModifiedOutsideIndia"] = "Yes"
                else:
                    send_to_json["whetherChargeIsCreatedOrModifiedOutsideIndia"] = "No"

        consortium = full_string.rfind("Whether consortium finance is involved")
        if consortium != -1:
            consortium_substring = full_string[consortium : consortium + 50]
            values = consortium_substring.find("@")
            if values != -1:
                value = consortium_substring[values : values + 4]
                if value.find("Y") != -1:
                    send_to_json["whetherConsortiumFinance"] = "Yes"
                else:
                    send_to_json["whetherConsortiumFinance"] = "No"

        joint = full_string.rfind("Whether joint charge")
        if joint != -1:
            joint_substring = full_string[joint : joint + 45]
            values = joint_substring.find("@")
            if values != -1:
                value = joint_substring[values : values + 4]
                if value.find("Y") != -1:
                    send_to_json["whetherJointChargeIsInvolved"] = "Yes"
                else:
                    send_to_json["whetherJointChargeIsInvolved"] = "No"

        propertys = full_string.rfind(
            "Whether any of the property or interest therein under reference is not reg"
        )
        if propertys != -1:
            propertys_substring = full_string[propertys : propertys + 133]
            values = propertys_substring.find("@")
            if values != -1:
                value = propertys_substring[values : values + 4]
                if value.find("Y") != -1:
                    send_to_json[
                        "whetherAnyOfTheIsNotRegisteredInTheNameOfTheCompany"
                    ] = "Yes"
                else:
                    send_to_json[
                        "whetherAnyOfTheIsNotRegisteredInTheNameOfTheCompany"
                    ] = "No"

        type_of_charge = ""
        test = []
        a = " ".join(page_2_text.split())
        b = a.split("8. (a) “Whether consortium")
        c = b[0]

        g = c.split("X")
        if len(g) == 1:
            d = c.split("|")
            for i, v in enumerate(d):
                h = v[0:14]
            test.append(h)
        else:
            for i, v in enumerate(g):
                h = v[0:12]
                test.append(h)

        to_check = {
            "Uncalled": "Uncalled share capital Calls made but not paid",
            "Immovable": "Immovable property or any interest therein",
            "Movable": "Movable property",
            "Floating": "Floating charge",
            "Motor": "Motor Vehicle (Hypothecation)",
            "Any": "Any property for securing the issue of secured deposits",
            "Goodwill": "Goodwill",
            "Patent": "Patent",
            "Licence": "Licence under a patent",
            "Trade": "Trade mark",
            "Copyright": "Copyright",
            "Book": "Book debts",
            "Ship": "Ship or any share in a ship",
            "Solely": "Solely of Property situated outside India",
            "Others": "Others",
        }

        keys_of_to_check = list(to_check.keys())

        for i, v in enumerate(test):

            for j, w in enumerate(keys_of_to_check):
                m = self.check_substring(v, w)
                if m != -1:
                    answer3.append(to_check.get(w, None))

        for i, v in enumerate(answer3):
            if i == 0:
                type_of_charge += v
            else:
                type_of_charge += " ," + v

        if len(type_of_charge) == 0:
            type_of_charge = None
        send_to_json["typeOfCharge"] = type_of_charge

        keys_of_formtextfields = [
            "CIN_C[0]",
            "ChargeId_C[0]",
            "Date_of_charge_creation_D[0]",
            "Instrumentdescription_C[0]",
            "Number_of_charges_N[0]",
            "Designation2[0]",
            "Amount_secured_N[0]",
            "RateOfInterest[0]",
            "RepaymentTerm[0]",
            "TermsOfRepayment[0]",
            "NatureFacility[0]",
            "Date_Disbursement_D[0]",
            "Margin[0]",
            "ExtentCharge[0]",
            "Short_Particulars[0]",
            "Particulars_of_modification_C[0]",
            "CHName_C[0]",
        ]

        add = [
            "CHaddressA_C[0]",
            "CHCity_C[0]",
            "CHaddressB_C[0]",
            "CHPin_C[0]",
            "CHCountry_C[0]",
        ]

        json_keys = [
            "cIN/FCRNOfTheCompany",
            "chargeIDOfTheChargeToBeModified",
            "dateOfTheInstrumentCreatingOrModifyingTheCharge",
            "natureDescriptionOfTheInstrument",
            "numberOfChargeHolder",
            "incometaxPermanentAccountNumber",
            "amountSecuredByCharge",
            "rateOfInterest",
            "repaymentTerm",
            "termsOfRepayment",
            "natureOfFacility",
            "dateOfDisbursement",
            "Margin",
            "Extent and operation of Charge",
            "Short particulars of the property or asset(s) charged",
            "particularsOfThePresentModification",
            "bankName",
        ]

        list_of_text_values_tojson = []
        address = ""

        ip_pdf = PyPDF2.PdfFileReader(self.path, "rb")
        ip_filled_data = OrderedDict(ip_pdf.getFormTextFields())

        for i in keys_of_formtextfields:
            list_of_text_values_tojson.append(ip_filled_data.get(i, None))

        for i in range(len(add)):
            if i < 1:
                if ip_filled_data.get(add[i], None) == None:
                    address += " "
                else:
                    address += ip_filled_data.get(add[i], None)
            else:
                if ip_filled_data.get(add[i], None) == None:
                    address += ", "
                else:
                    address += ", " + ip_filled_data.get(add[i], None)

        for i in range(len(json_keys)):
            temp = str(list_of_text_values_tojson[i])
            temp.encode().decode()
            send1[json_keys[i]] = temp

        if ip_filled_data.get("No_of_documents[0]", None) != None:
            address2 = ""
            documentNumber = ip_filled_data["Doc_Number[0]"]
            address2_keys = [
                "Doc_Taluka[0]",
                "ISO_Code[0]",
                "Doc_Pincode[0]",
            ]

            for i, v in enumerate(address2_keys):
                if i >= 1:
                    address2 += ", " + ip_filled_data[v]
                else:
                    address2 += ip_filled_data[v]

            temp1 = {"documentNumber": None, "address": None}
            temp1["documentNumber"] = documentNumber
            temp1["address"] = address2

            send1.__setitem__("descriptionOfDocumentByWhichCompanyAcquiredTheTitle", temp1)
        else:
            send1.__setitem__("descriptionOfDocumentByWhichCompanyAcquiredTheTitle", list())

        send1["address"] = address

        send1.update(send_to_json)

        return send1


if __name__ == '__main__':
    Obj = ChgOneForm("../data/Form CHG-1-01072016_signed.pdf")
    print(Obj.extract_parse_createjson_frompdf())
