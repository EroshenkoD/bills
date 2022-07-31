from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from calendar import monthrange
ifrom django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from calendar import monthrange
import gspread
import openpyxl
import pandas


GOOGLE_SHEET = '1j3gY4TLh6aQxrRZWTBZLNcBY7yTQ9ITeDscqhxEUeW8'
DICT_MONTH = {1: 'Січень(01)', 2: 'Лютий(02)', 3: 'Березень(03)', 4: 'Квітень(04)', 5: 'Травень(05)', 6: 'Червень(06)',
              7: 'Липень(07)', 8: 'Серпень(08)', 9: 'Вересень(09)', 10: 'Жовтень(10)', 11: 'Листопад(11)',
              12: 'Грудень(12)'}

DICT_ADDRESS = {'Lazyrna_7': 'вул. Лазурна, буд. 7'}

DICT_REPORT = {'debtor': 'Боржники'}


class ClientElectricBill(models.Model):

    LIST_ADDRESS = list((str(i), j) for i, j in DICT_ADDRESS.items())

    LIST_MONTH = list((str(i), j) for i, j in DICT_MONTH.items())

    curr_date = datetime.today()

    LIST_YEARS = [
        (str(curr_date.year - 1), curr_date.year - 1),
        (str(curr_date.year), curr_date.year),
        (str(curr_date.year + 1), curr_date.year + 1),
    ]

    numb_flat = models.PositiveSmallIntegerField(verbose_name="Квартира №", unique=True)
    name_contact_person = models.CharField('Контактна особа', max_length=50)
    phone_number = models.CharField('Номер телефону', max_length=20, blank=True, null=True)
    address_street = models.CharField(verbose_name="Вулиця", max_length=30, choices=LIST_ADDRESS,
                                      default=LIST_ADDRESS[0][1])
    is_active = models.BooleanField(verbose_name="Нараховувати оплату", default=True)
    month_start_pay_bill = models.CharField(verbose_name="Місяць", max_length=20, choices=LIST_MONTH,
                                            default=str(curr_date.month))
    year_start_pay_bill = models.CharField(verbose_name="Рік", max_length=5, choices=LIST_YEARS,
                                           default=str(curr_date.year))
    note = models.TextField('', max_length=150, blank=True, null=True)
    date_start_pay = models.DateField(blank=True, null=True)
    square_meters = models.PositiveSmallIntegerField(verbose_name="Площадь, кв.м.")
    square_meters_fractional = models.PositiveSmallIntegerField(verbose_name="Десяті", default=0)

    def __str__(self):
        return f'Кв. {self.numb_flat} / {self.name_contact_person}'
        #return f'Кв. {self.numb_flat} / {DICT_ADDRESS[str(self.address_street)]}'

    class Meta:
        verbose_name = "Квартира"
        verbose_name_plural = "Квартири"
        db_table = "numb_flat"
        ordering = ('numb_flat',)

    def clean(self, *args, **kwargs):
        self.clean_fields()
        date_start = make_date(self.month_start_pay_bill, self.year_start_pay_bill)
        self.date_start_pay = date_start
        if self.square_meters_fractional > 99:
            raise ValidationError({
                'square_meters_fractional': [
                    ValidationError(
                        message="Соті квадратного метра не можуть бути більше 99.",
                    )
                ]
            })

        try:
            cur_client = ClientElectricBill.objects.get(id=self.id)
        except Exception:
            cur_client = False
        if cur_client:
            if cur_client.square_meters_fractional != self.square_meters_fractional:
                raise ValidationError({
                    'square_meters_fractional': [
                        ValidationError(
                            message="Змінювати площу квартири заборонено!",
                        )
                    ]
                })
            if cur_client.square_meters != self.square_meters:
                raise ValidationError({
                    'square_meters': [
                        ValidationError(
                            message="Змінювати площу квартири заборонено!",
                        )
                    ]
                })
            if cur_client.numb_flat != self.numb_flat:
                raise ValidationError({
                    'numb_flat': [
                        ValidationError(
                            message="Змінювати номер квартири заборонено!",
                        )
                    ]
                })

            if cur_client.address_street != self.address_street:
                raise ValidationError({
                    'address_street': [
                        ValidationError(
                            message="Змінювати адресу квартири заборонено!",
                        )
                    ]
                })


class TariffForBill (models.Model):
    LIST_MONTH = ClientElectricBill.LIST_MONTH
    LIST_YEARS = ClientElectricBill.LIST_YEARS

    month_start_tariff_bill = models.CharField(verbose_name="Від місяць", max_length=20, choices=LIST_MONTH)
    year_start_tariff_bill = models.CharField(verbose_name="рік", max_length=5, choices=LIST_YEARS)
    month_end_tariff_bill = models.CharField(verbose_name="До місяць", max_length=20, choices=LIST_MONTH)
    year_end_tariff_bill = models.CharField(verbose_name="рік", max_length=5, choices=LIST_YEARS)
    sum_tariff_to_pay = models.PositiveSmallIntegerField(verbose_name="Сума тарифу, грн.")
    sum_tariff_to_pay_cop = models.PositiveSmallIntegerField(verbose_name="Сума тарифу, коп.")
    date_start_tariff = models.DateField(blank=True, null=True)
    date_end_tariff = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'Тариф {self.sum_tariff_to_pay} грн. діє з {DICT_MONTH[int(self.month_start_tariff_bill)]}' \
               f' {self.year_start_tariff_bill}' \
               f'  по ' \
               f'{DICT_MONTH[int(self.month_end_tariff_bill)]} {self.year_end_tariff_bill} включно'

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифи"
        db_table = "tariff"
        ordering = ('-year_start_tariff_bill', '-month_start_tariff_bill')

    def clean(self, *args, **kwargs):
        self.clean_fields()
        date_start = make_date(self.month_start_tariff_bill, self.year_start_tariff_bill)
        self.date_start_tariff = date_start
        date_end = make_date(self.month_end_tariff_bill, self.year_end_tariff_bill)
        self.date_end_tariff = date_to_end_month(date_end)
        if date_start > date_end:
            raise ValidationError({
                'month_start_tariff_bill': [
                    ValidationError(
                        message="Дата початку дії таруфу не може бути пізніше дати припинення дії тарифу",
                    )
                ]
            })
        try:
            cur_tariff = TariffForBill.objects.get(id=self.id)
        except Exception:
            cur_tariff = False
        if cur_tariff:
            if cur_tariff.sum_tariff_to_pay_cop != self.sum_tariff_to_pay_cop:
                raise ValidationError({
                    'sum_tariff_to_pay_cop': [
                        ValidationError(
                            message="Коригувати дозволяеться тільки дату припинення дії тарифу",
                        )
                    ]
                })
            if cur_tariff.sum_tariff_to_pay != self.sum_tariff_to_pay:
                raise ValidationError({
                    'sum_tariff_to_pay': [
                        ValidationError(
                            message="Коригувати дозволяеться тільки дату припинення дії тарифу",
                        )
                    ]
                })
            last_tariff = TariffForBill.objects.all().order_by('date_end_tariff').last()
            if cur_tariff.id == last_tariff.id:
                date_start_last_tariff = make_date(last_tariff.month_start_tariff_bill,
                                                   last_tariff.year_start_tariff_bill)
                date_end_last_tariff = make_date(last_tariff.month_end_tariff_bill, last_tariff.year_end_tariff_bill)
                if date_start_last_tariff != date_start:
                    raise ValidationError({
                        'month_start_tariff_bill': [
                            ValidationError(
                                message="Коригувати дозволяеться тільки дату припинення дії тарифу",
                            )
                        ]
                    })
                if date_end_last_tariff > date_end:
                    raise ValidationError({
                        'month_end_tariff_bill': [
                            ValidationError(
                                message="Дату припинення дії тарифу дозволяеться тільки продовжувувати.",
                            )
                        ]
                    })
            else:
                raise ValidationError({
                    'month_start_tariff_bill': [
                        ValidationError(
                            message="Коригувати дозволяеться тільки крайній тариф.",
                        )
                    ]
                })
        else:
            try:
                last_tariff = TariffForBill.objects.all().order_by('date_end_tariff').last()
            except Exception:
                last_tariff = False
            if last_tariff:
                date_end_last_tariff = make_date(last_tariff.month_end_tariff_bill, last_tariff.year_end_tariff_bill)
                date_start_next_tariff = next_month_date(date_end_last_tariff)
                if date_start_next_tariff != date_start:
                    raise ValidationError({
                        'month_start_tariff_bill': [
                            ValidationError(
                                message="Дата початку дії нового тарифу повинна бути дата початку наступного місяця "
                                        "після "
                                        "припинення дії попереднього тарифу.",
                            )
                        ]
                    })


class PayElectricBill(models.Model):

    client = models.ForeignKey(ClientElectricBill, verbose_name="Клиент", on_delete=models.PROTECT)
    month_start_pay_bill = models.CharField(verbose_name="Від місяць", max_length=20, blank=True, null=True)
    year_start_pay_bill = models.CharField(verbose_name="рік", max_length=5, blank=True, null=True)
    month_end_pay_bill = models.CharField(verbose_name="До місяць", max_length=20, blank=True, null=True)
    year_end_pay_bill = models.CharField(verbose_name="рік", max_length=5, blank=True, null=True)
    date_pay = models.DateTimeField(verbose_name='Дата оплати', default=datetime.now())
    sum_to_pay = models.CharField(verbose_name="Сума оплати, грн.", max_length=20, blank=True, null=True)
    col_month_to_pay = models.PositiveSmallIntegerField(verbose_name="Кількість місяців до сплати")
    date_start_pay = models.DateField(blank=True, null=True)
    date_end_pay = models.DateField(blank=True, null=True)

    def __str__(self):
        return f' {self.date_pay} / {self.sum_to_pay}'

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплати"
        db_table = "pay_electric_bill"
        ordering = ('date_pay',)

    def clean(self, *args, **kwargs):
        self.clean_fields()
        if not self.client.is_active:
            raise ValidationError({
                'client': [
                    ValidationError(
                        message=f"Кліенту {self.client.__str__()} не нараховуються оплати!",
                    )
                ]
            })

        try:
            cur_bill_pay = PayElectricBill.objects.get(id=self.id)
        except Exception:
            cur_bill_pay = False
        if cur_bill_pay:
            try:
                last_bill_pay = PayElectricBill.objects.filter(client_id=self.client_id).order_by('date_end_pay').last()
            except Exception:
                last_bill_pay = False
            if last_bill_pay:
                if cur_bill_pay.id != last_bill_pay.id:
                    raise ValidationError({
                        'client': [
                            ValidationError(
                                message="Коригувати дозволяеться тільки останню оплату кліента.",
                            )
                        ]
                    })
        else:
            try:
                last_bill_pay = PayElectricBill.objects.filter(client_id=self.client_id).order_by('date_end_pay').last()
            except Exception:
                last_bill_pay = False
            month_date_start = self.client.month_start_pay_bill
            year_date_start = self.client.year_start_pay_bill
            self.date_start_pay = make_date(month_date_start, year_date_start)
            if last_bill_pay:
                if last_bill_pay.date_end_pay > self.date_start_pay:
                    self.date_start_pay = last_bill_pay.date_end_pay + timedelta(days=1)
        self.month_start_pay_bill = DICT_MONTH[self.date_start_pay.month]
        self.year_start_pay_bill = self.date_start_pay.year
        if self.col_month_to_pay == 0:
            raise ValidationError({
                'col_month_to_pay': [
                    ValidationError(
                        message="Кількість місяців оплати не може дорівнювати 0.",
                    )
                ]
            })
        temp = self.col_month_to_pay - 1
        temp_date_end_pay = self.date_start_pay
        while True:
            if temp == 0:
                break
            temp_date_end_pay = next_month_date(temp_date_end_pay)
            temp -= 1
        self.date_end_pay = date_to_end_month(temp_date_end_pay)
        self.month_end_pay_bill = DICT_MONTH[self.date_end_pay.month]
        self.year_end_pay_bill = self.date_end_pay.year
        temp_sum_to_pay = sum_to_pay_funk(self.date_start_pay, self.date_end_pay, self.client)
        if temp_sum_to_pay[0]:
            raise ValidationError({
                'client': [
                    ValidationError(
                        message=temp_sum_to_pay[0],
                    )
                ]
            })
        self.sum_to_pay = temp_sum_to_pay[4]


class Report(models.Model):

    LIST_REPORT = list((str(i), j) for i, j in DICT_REPORT.items())
    LIST_MONTH = list((str(i), j) for i, j in DICT_MONTH.items())

    curr_date = datetime.today()

    LIST_YEARS = [
        (str(curr_date.year - 1), curr_date.year - 1),
        (str(curr_date.year), curr_date.year),
        (str(curr_date.year + 1), curr_date.year + 1),
    ]
    type_report = models.CharField(verbose_name="Тип звіту", max_length=30, choices=LIST_REPORT,
                                   default=LIST_REPORT[0][1])
    month_till_report = models.CharField(verbose_name="Місяць", max_length=20, choices=LIST_MONTH,
                                         default=str(curr_date.month))
    year_till_report = models.CharField(verbose_name="Рік", max_length=5, choices=LIST_YEARS,
                                        default=str(curr_date.year))

    def clean(self, *args, **kwargs):
        gs = gspread.service_account(filename='key_google_docs.json')
        sh = gs.open_by_key(GOOGLE_SHEET)
        worksheet = sh.sheet1
        res = worksheet.get_all_values()
        if res:
            raise ValidationError({
                'type_report': [
                    ValidationError(
                        message="В Excel таблиці присутні данні!",
                    )
                ]
            })

        date_create_report = datetime.today()
        temp = ['Номер квартири', 'Остання оплата', 'Кількість місяців до сплати', 'Від дати',
                'До дати', 'Заборгованість, грн']
        data_list = [[], [f'Дата створення звіту: {date_create_report.strftime("%d-%m-%Y %H:%M:%S")}'],
                     [f'Назва звіту: {DICT_REPORT[self.type_report]}'], [], temp]

        all_sum_to_pay = 0.0
        till_date_report = make_date(self.month_till_report, self.year_till_report)
        till_date_report = date_to_end_month(till_date_report)
        list_client_obj = ClientElectricBill.objects.filter(is_active=True).order_by('numb_flat')
        for obj in list_client_obj:

            all_sum_to_pay
            try:
                date_last_pay = PayElectricBill.objects.filter(client_id=obj.id).order_by('date_end_pay').\
                    last().date_end_pay
                #first_date_to_pay = next_month_date(date_last_pay)
                first_date_to_pay = make_date(date_last_pay.month, date_last_pay.year)
                first_date_to_pay = next_month_date(first_date_to_pay)
                date_last_pay = f'{DICT_MONTH[date_last_pay.month]} {date_last_pay.year}'
            except Exception:
                date_last_pay = False

            if not date_last_pay:
                date_last_pay = 'Оплат ще не було!'
                first_date_to_pay = obj.date_start_pay
            else:
                if first_date_to_pay < obj.date_start_pay:
                    first_date_to_pay = obj.date_start_pay
            if first_date_to_pay < till_date_report:
                sym_to_pay = sum_to_pay_funk(first_date_to_pay, till_date_report, obj)
                if sym_to_pay[0]:
                    raise ValidationError({
                        'type_report': [
                            ValidationError(
                                message=sym_to_pay[0],
                            )
                        ]
                    })
                all_sum_to_pay += sym_to_pay[5]
                all_sum_to_pay = round(all_sum_to_pay, 2)
                temp_data = [obj.__str__(),  date_last_pay, sym_to_pay[2],
                             f'{DICT_MONTH[first_date_to_pay.month]} {first_date_to_pay.year}',
                             f'{DICT_MONTH[till_date_report.month]} {till_date_report.year}', sym_to_pay[4]]
            else:
                temp_data = [obj.__str__(), date_last_pay, 'Заборгованості відсутні']
            data_list.append(temp_data)
        temp = [f'Загальна сума заборгованості складае: {all_sum_to_pay} грн.']
        data_list.append([])
        data_list.append(temp)
        workbook = openpyxl.Workbook()
        sheet = workbook['Sheet']
        for i in range(len(data_list)):
            for j in range(len(data_list[i])):
                sheet.cell(row=i+1, column=j+1).value = data_list[i][j]

        workbook.save('my_file.xlsx')
        workbook.close()

        data_xls = pandas.read_excel('my_file.xlsx', index_col=0)
        data_xls.to_csv('my_file.csv', encoding='utf-8')
        try:
            content = open("my_file.csv", "r").read().encode('cp1251').decode('utf-8')
        except Exception:
            content = open("my_file.csv", "r").read().encode('utf-8')

        gs.import_csv(GOOGLE_SHEET, content)

        gs = gspread.service_account(filename='key_google_docs.json')
        sh = gs.open_by_key(GOOGLE_SHEET)
        worksheet = sh.sheet1

        worksheet.delete_rows(1)

    class Meta:
        verbose_name = "Звіт"
        verbose_name_plural = "Звіти"
        db_table = "report"

    def save(self, *args, **kwargs):
        pass


class Privilege(models.Model):

    LIST_MONTH = ClientElectricBill.LIST_MONTH
    LIST_YEARS = ClientElectricBill.LIST_YEARS

    client = models.ForeignKey(ClientElectricBill, verbose_name="Клиент", on_delete=models.PROTECT)
    month_start_tariff_bill = models.CharField(verbose_name="Від місяць", max_length=20, choices=LIST_MONTH)
    year_start_tariff_bill = models.CharField(verbose_name="рік", max_length=5, choices=LIST_YEARS)
    month_end_tariff_bill = models.CharField(verbose_name="До місяць", max_length=20, choices=LIST_MONTH)
    year_end_tariff_bill = models.CharField(verbose_name="рік", max_length=5, choices=LIST_YEARS)
    percent = models.PositiveSmallIntegerField(verbose_name="Процентов")
    date_start_tariff = models.DateField(blank=True, null=True)
    date_end_tariff = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'{self.client.__str__()} льгота складає {self.percent}%'

    class Meta:
        verbose_name = "Льгота"
        verbose_name_plural = "Льготи"
        db_table = "privilege"
        ordering = ('-year_start_tariff_bill', '-month_start_tariff_bill')

    def clean(self, *args, **kwargs):
        if self.percent > 100:
            raise ValidationError({
                'percent': [
                    ValidationError(
                        message="Льготии не можуть перевищувати знижку у 100%.",
                    )
                ]
            })
        self.clean_fields()
        date_start = make_date(self.month_start_tariff_bill, self.year_start_tariff_bill)
        self.date_start_tariff = date_start
        date_end = make_date(self.month_end_tariff_bill, self.year_end_tariff_bill)
        self.date_end_tariff = date_to_end_month(date_end)
        if date_start > date_end:
            raise ValidationError({
                'month_start_tariff_bill': [
                    ValidationError(
                        message="Дата початку дії льгот не може бути пізніше дати припинення дії льгот.",
                    )
                ]
            })
        try:
            date_last_pay = Privilege.objects.filter(client_id=self.id).order_by('date_end_pay').last().date_end_pay
        except Exception:
            date_last_pay = False
        if date_last_pay:
            if date_start < date_last_pay:
                raise ValidationError({
                    'month_start_tariff_bill': [
                        ValidationError(
                            message="Льготи не можуть починати діяти раніше дати останьої оплати клієнта.",
                        )
                    ]
                })

        try:
            date_last_privilege = PayElectricBill.objects.filter(client_id=self.id).order_by('date_end_tariff').\
                last().date_end_tariff
        except Exception:
            date_last_privilege = False
        if date_last_privilege:
            if date_start < date_last_privilege:
                raise ValidationError({
                    'date_start_tariff': [
                        ValidationError(
                            message="Дата нового льготного періоду не може починатися раніше вже існуючого.",
                        )
                    ]
                })


def next_month_date(date):
    add_days = monthrange(date.year, date.month)[1]
    return date + timedelta(days=add_days)


def make_date(month, year):
    for key in DICT_MONTH.keys():
        if str(month) == str(key):
            numb_month = key
            if key < 10:
                numb_month = f'0{key}'
            break
    return datetime.strptime(f'{year}{numb_month}01', '%Y%m%d').date()


def sum_to_pay_funk(date_start, date_end, obj_client):
    err = False
    sum_to_pay_all = 0.0
    col_month = 0
    cur_date_for_calculation = date_start
    while cur_date_for_calculation < date_end:
        try:
            cur_tariff = TariffForBill.objects.get(date_start_tariff__lte=cur_date_for_calculation,
                                                   date_end_tariff__gte=cur_date_for_calculation)
        except Exception:
            err = f"Не вказані тарифи для {DICT_MONTH[cur_date_for_calculation.month]} {cur_date_for_calculation.year}"
            break
        try:
            privilege = Privilege.objects.get(client_id=obj_client.id, date_start_tariff__lte=cur_date_for_calculation,
                                              date_end_tariff__gte=cur_date_for_calculation).percent
        except Exception:
            privilege = False
        tariff_pay = float(f'{cur_tariff.sum_tariff_to_pay}.{cur_tariff.sum_tariff_to_pay_cop}')
        if privilege:
            tariff_pay -= tariff_pay * privilege / 100
        if tariff_pay > 0:
            float(tariff_pay)
            sum_to_pay_all += tariff_pay * float(str(obj_client.square_meters)+"."+str(obj_client.square_meters_fractional))
        col_month += 1
        cur_date_for_calculation = next_month_date(cur_date_for_calculation)
    sum_to_pay_all = round(sum_to_pay_all, 2)
    str_sum_pay = str(sum_to_pay_all)
    temp = str_sum_pay.split('.')
    sum_to_pay = int(temp[0])
    sum_to_pay_cop = int(temp[1])
    return [err, sum_to_pay, col_month, sum_to_pay_cop, str_sum_pay, sum_to_pay_all]


def date_to_end_month(date):
    date_year = date.year
    date_month = date.month
    date_days = monthrange(date_year, date_month)[1] - 1
    date_end_month = date + timedelta(days=date_days)
    return date_end_month



