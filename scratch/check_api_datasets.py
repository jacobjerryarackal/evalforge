import urllib.request
import json

def main():
    try:
        res = urllib.request.urlopen('http://localhost:8000/api/datasets')
        data = json.loads(res.read().decode())
        print(f"Total Datasets returned by API: {len(data)}")
        for d in data:
            print(f"  Dataset ID: {d['dataset_id']:30} | Version: {d['version']}")
    except Exception as e:
        print(f"Failed to query API: {e}")

if __name__ == "__main__":
    main()
