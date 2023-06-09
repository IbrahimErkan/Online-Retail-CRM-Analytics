###############################################################
# 1. İş Problemi (Business Problem)
###############################################################

# Bir e-ticaret şirketi müşterilerini segmentlere ayırıp bu segmentlere göre pazarlama stratejileri belirlemek istiyor.

# Veri Seti Hikayesi
# online_retail_II.xlsx

# Online Retail II isimli veri seti İngiltere merkezli online bir satış mağazasının
# 01/12/2009 - 09/12/2011 tarihleri arasındaki satışlarını içeriyor.


# Değişkenler
#
# InvoiceNo: Fatura numarası. Her işleme yani faturaya ait eşsiz numara. C ile başlıyorsa iptal edilen işlem.
# StockCode: Ürün kodu. Her bir ürün için eşsiz numara.
# Description: Ürün ismi.
# Quantity: Ürün adedi. Fatulardaki ürünlerden kaçar tane satıldığını ifade etmektedir.
# InvoiceDate: Fatura tarihi ve zamanı.
# UnitPrice: Ürün fiyatı (Sterlin cinsinden)
# CustomerID: Eşsiz müşteri numarası.
# Country: Ülke ismi. Müşterinin yaşadığı ülke.



###############################################################
# 2. Veriyi Anlama (Data Understanding)
###############################################################

import datetime as dt
import pandas as pd
pd.set_option('display.max_columns', None)                    #tüm sütunları göster
# pd.set_option('display.max_rows', None)                     #tüm satırları göster
pd.set_option('display.float_format', lambda x: '%.3f' % x)   #sayısal değişkenlerin, virgülden sonra kaç basamağını gösterir

df_ = pd.read_excel("Online Retail CRM Analytics/datasets/online_retail_II.xlsx", sheet_name= "Year 2010-2011")
df = df_.copy()
df.head()
df.shape
df.isnull().sum()

# eşsiz urun sayisi nedir?
df["Description"].nunique()

df["Description"].value_counts().head()

# toplam ne kadar sipariş verildi?
df.groupby("Description").agg({"Quantity": "sum"}).sort_values("Quantity", ascending=False).head()

df["Invoice"].nunique()

df["TotalPrice"] = df["Quantity"] * df["Price"]

df.groupby("Invoice").agg({"TotalPrice": "sum"}).head()



###############################################################
# 3. Veriyi Hazırlama (Data Preparation)
###############################################################

df.shape
df.isnull().sum()
df.dropna(inplace=True)
df.describe().T

df = df[~df["Invoice"].str.contains("C", na=False)]



###############################################################
# 4. RFM Metriklerinin Hesaplanması (Calculating RFM Metrics)
###############################################################

# Recency, Frequency, Monetary  (yenilik, sıklık, parasal deger)
df.head()

df["InvoiceDate"].max()

today_date = dt.datetime(2011, 12, 11)
type(today_date)

rfm = df.groupby("Customer ID").agg({'InvoiceDate': lambda InvoiceDate: (today_date - InvoiceDate.max()).days,  # recency
                           'Invoice': lambda Invoice: Invoice.nunique(),       # frequency
                           'TotalPrice': lambda TotalPrice: TotalPrice.sum()})     # monetary

rfm.head()

rfm.columns = ['recency', 'frequency', 'monetary']

rfm.describe().T

rfm = rfm[rfm["monetary"] > 0]

rfm.shape



###############################################################
# 5. RFM Skorlarının Hesaplanması (Calculating RFM Scores)
###############################################################

rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])

# 0-100, 0-20, 20-40,40-60, 60-80, 80-100

rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])

rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])


rfm["RF_SCORE"] = (rfm['recency_score'].astype(str) +
                    rfm['frequency_score'].astype(str))

rfm.describe().T

rfm[rfm["RF_SCORE"] == "55"]
rfm[rfm["RF_SCORE"] == "11"]



###############################################################
# 6. RFM Segmentlerinin Oluşturulması ve Analiz Edilmesi (Creating & Analysis RFM Segmnets)
###############################################################

# regex

# RFM isimlendirmesi
seg_map = {
    r'[1-2][1-2]': 'hipernating',
    r'[1-2][3-4]': 'at_Risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
}

rfm['segment'] = rfm['RF_SCORE'].replace(seg_map, regex=True)

rfm[['segment', 'recency', 'frequency', 'monetary']].groupby("segment").agg(['mean', 'count'])

rfm[rfm["segment"] == "need_attention"].head()
rfm[rfm["segment"] == "cant_loose"].head()
rfm[rfm["segment"] == "cant_loose"].index

new_df =pd.DataFrame()
new_df["new_customer_id"] = rfm[rfm["segment"] == "new_customers"].index

new_df["new_customer_id"] = new_df["new_customer_id"].astype(int)


new_df.to_csv("new_customers.csv")

rfm.to_csv("rfm.csv")



###############################################################
# 7. Tüm Sürecin Fonksiyonlaştırılması
###############################################################

def create_rfm(dataframe, csv=False):

    # VERIYI HAZIRLAMA
    dataframe['TotalPrice'] = dataframe["Quantity"] * dataframe["Price"]
    dataframe.dropna(inplace=True)
    dataframe = dataframe[~dataframe["Invoice"].str.contains("C", na=False)]

    # RFM METRIKLERININ HESAPLANMASI
    today_date = dt.datetime(2011, 12, 11)
    rfm = df.groupby("Customer ID").agg({'InvoiceDate': lambda date: (today_date - date.max()).days,
                                        'Invoice': lambda num: num.nunique(),
                                        'TotalPrice': lambda price: price.sum()})
    rfm.columns = ["recency", "frequency", "monetary"]
    rfm = rfm[(rfm["monetary"] > 0)]

    # RFM SKORLARININ HESAPLANMASI
    rfm["recency_score"] = pd.qcut(rfm['recency'], 5, labels=[5, 4, 3, 2, 1])
    rfm["frequency_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])
    rfm["monetary_score"] = pd.qcut(rfm['monetary'], 5, labels=[1, 2, 3, 4, 5])

    # cltv_df skorları kategorik degere dönüştürülüp df'e eklendi
    rfm["RF_SCORE"] = (rfm['recency_score'].astype(str) +
                       rfm['frequency_score'].astype(str))

    # SEGMENTLERIN ISIMLENDIRILMESI
    seg_map = {
        r'[1-2][1-2]': 'hipernating',
        r'[1-2][3-4]': 'at_Risk',
        r'[1-2]5': 'cant_loose',
        r'3[1-2]': 'about_to_sleep',
        r'33': 'need_attention',
        r'[3-4][4-5]': 'loyal_customers',
        r'41': 'promising',
        r'51': 'new_customers',
        r'[4-5][2-3]': 'potential_loyalists',
        r'5[4-5]': 'champions'
    }

    rfm['segment'] = rfm['RF_SCORE'].replace(seg_map, regex=True)
    rfm = rfm[["recency", "frequency", "monetary", "segment"]]

    rfm.index = rfm.index.astype(int)

    if csv:
        rfm.to_csv(rfm.csv)

    return rfm


df = df_.copy()

rfm_new = create_rfm(df)