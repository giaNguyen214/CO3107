
from pymongo import MongoClient

def upload_to_mongo(data, db_name="faymuni", collection_name="sensor_data"):
    try:
        # Connect
        client = MongoClient('<None>')
        db = client[db_name]  
        collection = db[collection_name]  

        # ADD
        if data:
            result = collection.insert_many(data)
            print(f"Đã chèn {len(result.inserted_ids)} tài liệu vào MongoDB.")
        else:
            print("Dữ liệu trống.")
    except Exception as e:
        print(f"Đã xảy ra lỗi khi kết nối hoặc tải dữ liệu lên MongoDB: {e}")
