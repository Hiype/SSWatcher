import requests
from bs4 import BeautifulSoup
import time
import json
import hashlib
import os


class SSComMonitor:
    def __init__(self):
        self.url = "https://www.ss.com/lv/transport/cars/audi/a7/fDgSeF4belM=.html"
        self.onesignal_app_id = os.getenv('ONESIGNAL_REST_API_KEY')
        self.onesignal_rest_api_key = os.getenv('ONESIGNAL_REST_API_KEY')
        self.storage_file = 'known_ads.json'
        self.known_ads = self.load_known_ads()

    def load_known_ads(self):
        try:
            with open(self.storage_file, 'r') as f:
                return set(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            return set()

    def save_known_ads(self):
        with open(self.storage_file, 'w') as f:
            json.dump(list(self.known_ads), f)

    def get_page_content(self):
        try:
            response = requests.get(self.url)
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching page: {e}")
            return None

    def parse_ads(self, soup):
        ads = []
        if soup:
            listings = soup.select('tr[id^="tr_"]')
            for listing in listings:
                title_elem = listing.select_one('td.msg2 a')
                thumbnail = listing.select_one('img.isfoto')

                if not title_elem or (thumbnail and thumbnail.get('src', '').lower().endswith('.gif')):
                    continue

                if title_elem:
                    title = title_elem.text.strip()
                    url = f"https://www.ss.com{title_elem['href']}"
                    ad_id = hashlib.md5(title.encode()).hexdigest()

                    try:
                        ad_response = requests.get(url)
                        ad_soup = BeautifulSoup(ad_response.content, 'html.parser')

                        # Find first link containing image with class "isfoto"
                        full_img_link = ad_soup.select_one('a:has(img.isfoto)')
                        img_url = full_img_link['href'] if full_img_link else ''

                        # Convert relative URL to absolute if needed
                        if img_url and not img_url.startswith('http'):
                            img_url = f"https://www.ss.com{img_url}"

                    except Exception as e:
                        print(f"Error fetching ad details: {e}")
                        img_url = ''

                    ads.append({
                        'id': ad_id,
                        'title': title,
                        'img_url': img_url,
                        'url': url
                    })
        return ads

    def send_notification(self, title, image_url, url):  # Add url parameter
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Key {self.onesignal_rest_api_key}'
        }

        payload = {
            'app_id': self.onesignal_app_id,
            'included_segments': ['All'],
            'contents': {'en': title},
            'headings': {'en': 'New Audi A7 listing!'},
            'big_picture': image_url,
            'chrome_web_image': image_url,
            'ios_attachments': {'id': image_url},
            'chrome_web_icon': 'https://hiype.id.lv/imgs/sslogo.png',
            'android_small_icon': 'https://hiype.id.lv/imgs/sslogo.png',
            'android_large_icon': 'https://hiype.id.lv/imgs/sslogo.png',
            'url': url
        }

        try:
            response = requests.post(
                'https://onesignal.com/api/v1/notifications',
                headers=headers,
                json=payload
            )
            print(f"Notification sent: {response.status_code}")

            if response.status_code != 200:
                print(f"Notification sending failed! Error: {response.json()}")
        except Exception as e:
            print(f"Error sending notification: {e}")

    def monitor(self):
        print("Starting monitoring...")
        while True:
            print("Checking for new ads...")

            soup = self.get_page_content()
            current_ads = self.parse_ads(soup)

            for ad in current_ads:
                if ad['id'] not in self.known_ads:
                    print(f"New ad found: {ad['title']}")
                    self.send_notification(ad['title'], ad['img_url'], ad['url'])
                    self.known_ads.add(ad['id'])
                    self.save_known_ads()

            time.sleep(300)


if __name__ == '__main__':
    monitor = SSComMonitor()
    monitor.monitor()