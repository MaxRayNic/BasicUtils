s = "vin|year|make|model|trim|dealer_name|dealer_street|dealer_city|dealer_state|dealer_zip|listing_price|listing_mileage|used|certified|style|driven_wheels|engine|fuel_type|exterior_color|interior_color|seller_website|first_seen_date|last_seen_date|dealer_vdp_last_seen_date|listing_status"
s2 = 'KNAFK4A61F5428652|2015|Kia|FORTE|LX|X Nation Auto Group|6003 Bandera Rd|San Antonio|TX|78238||53960|TRUE|FALSE|4D Sedan|FWD|1.8L||Silver|Gray|https://xnationautogroup.com|2021-11-24|2022-08-17|2022-08-17|'

import pandas as pd

import sqlalchemy

engine = sqlalchemy.create_engine('postgresql://postgres:password1234@localhost:5432/CarAudit')


i = 0

for chunk in pd.read_csv("/NEWTEST-inventory-listing-2022-08-17.csv", sep='|', chunksize=100000,index_col=False):

    chunk.to_sql('car_details', con=engine, if_exists='append',index=False)
    print(f'iteration {i} successfull')


