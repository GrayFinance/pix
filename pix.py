# Copyright (c) 2022 Walef Andrade de Souza Dias
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from re import findall
import crc16

# PIX code field identifier table
# defined by the central bank of Brazil.
ID_PAYLOAD_FORMAT_INDICATOR = "00"
ID_POINT_OF_INITIATION_METHOD = "01"
ID_MERCHANT_ACCOUNT_INFORMATION = "26"
ID_MERCHANT_ACCOUNT_INFORMATION_GUI = "00"
ID_MERCHANT_ACCOUNT_INFORMATION_KEY = "01"
ID_MERCHANT_ACCOUNT_INFORMATION_DESCRIPTION = "02"
ID_MERCHANT_ACCOUNT_INFORMATION_URL = "25"
ID_MERCHANT_CATEGORY_CODE = "52"
ID_TRANSACTION_CURRENCY = "53"
ID_TRANSACTION_AMOUNT = "54"
ID_COUNTRY_CODE = "58"
ID_MERCHANT_NAME = "59"
ID_MERCHANT_CITY = "60"
ID_POSTAL_CODE = "61"
ID_ADDITIONAL_DATA_FIELD_TEMPLATE = "62"
ID_ADDITIONAL_DATA_FIELD_TEMPLATE_TXID = "05"
ID_CRC16 = "63"

class Pix:

    def left_zero(self, data: str) -> str:
        """Returns a string the length of 'date' padded with leading zeros."""
        return str(len(data)).zfill(2)

    def transform(self, identify: str, value: str) -> str:
        """Concatenates the identifier and the value"""
        return identify + str(len(value.__str__())).zfill(2) + value.__str__()

    def encode(
        self,
        address: str,
        amount: float,
        name: str = "",
        city="SP",
        txid=None,
        label="",
    ) -> str:
        """
        Encodes the Pix data into a Pix code string and returns the result.
        """
        code = self.transform(ID_PAYLOAD_FORMAT_INDICATOR, "01")
        gui = self.transform(ID_MERCHANT_ACCOUNT_INFORMATION_GUI, "BR.GOV.BCB.PIX")
        key = self.transform(ID_MERCHANT_ACCOUNT_INFORMATION_KEY, address)
        lab = ""
        if label:
            lab = self.transform(ID_MERCHANT_ACCOUNT_INFORMATION_DESCRIPTION, label)

        code += self.transform(ID_MERCHANT_ACCOUNT_INFORMATION, f"{gui}{key}{lab}")
        code += self.transform(ID_MERCHANT_CATEGORY_CODE, "0000")
        code += self.transform(ID_TRANSACTION_CURRENCY, "986")
        code += self.transform(ID_TRANSACTION_AMOUNT, f"{amount:.2f}")
        code += self.transform(ID_COUNTRY_CODE, "BR")
        code += self.transform(ID_MERCHANT_NAME, name[:25].title())
        code += self.transform(ID_MERCHANT_CITY, city)

        if txid:
            txid = self.transform(ID_ADDITIONAL_DATA_FIELD_TEMPLATE_TXID, txid)
        else:
            txid = self.transform(ID_ADDITIONAL_DATA_FIELD_TEMPLATE_TXID, "***")

        code += self.transform(ID_ADDITIONAL_DATA_FIELD_TEMPLATE, txid)
        code += "6304"

        crc = crc16.crc16xmodem(bytes(code, "utf-8"), 0xFFFF)
        crc = "{:04X}".format(crc & 0xFFFF)
        return f"{code}{crc}"

    def get_address(self, pix: str) -> str:
        """Extracts and returns the Pix address from the provided
        Pix code string."""
        if "BR.GOV.BCB.PIX" in pix:
            index = pix.find("BR.GOV.BCB.PIX") + 16
        else:
            index = pix.find("br.gov.bcb.pix") + 16

        length = pix[index:][:2]
        if length[0] == "0":
            length = length[-1]

        length = int(length)
        return pix[index + 2 :][:length]

    def get_amount(self, pix: str) -> float:
        """Extracts and returns the Pix value from the provided
        Pix code string."""
        data = findall("54[0-9][0-9][0-9]*\.?[0-9]+58", pix)[-1]
        index = 4
        length = data[:2]
        if length[0] == "0":
            length = length[-1]

        length = int(length)
        return float(data[index:length][:-2])

    def get_name(self, pix: str) -> str:
        """Extracts the full name from a PIX key and returns it."""
        return findall(f"{ID_MERCHANT_NAME}[0-9]+([A-Za-z ]+)", pix)[-1]

    def decode(self, pix: str) -> dict:
        """Decodes the Pix code string and returns a dictionary with
        the address and value of the Pix.
        """
        address = self.get_address(pix)
        amount = self.get_amount(pix)
        name = self.get_name(pix)
        return {"address": address, "amount": amount, "name": name}
