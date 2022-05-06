import requests

# send log to Amplitude, where event_type - type log, user_id - player_id, time - time received log


def send_log():
    http_route = 'https://api2.amplitude.com/2/httpapi'
    headers = {
        'Content-Type': 'application/json',
        'Accept': '*/*'
    }
    data_for_post = {
        "api_key": "d464b52b7dbf0fc8956f53709875071b",
        "events": [
            {
                "user_id": "40203",
                "device_id": "123212-F01A-4BD9-95C6-8E5357DF265D",
                "event_type": "log_device_parameters",
                "language": "UA",
                "country": "Ukraine",
                "region": "Kiev obl.",
                "city": "Kiev",
                "dma": "DMA data",
                "platform": "PC",
                "version_name": "FW_001",
                "os": "Win 10.12",
                "session_id": 1634561149458,
                "time": 1640995200,
                "event_properties": {
                    "load_time": 0.8371,
                    "source": "test_pc",
                    "dates": [
                        "noW",
                        "tuesday"
                    ]
                },
                "user_properties": {
                    "Session ID": 500000,
                    "Source": "test_pc"}
            }
        ]
    }
    z = str(data_for_post)
    print(str(data_for_post))
    r = requests.post(http_route, data=str(data_for_post).encode('utf-8'), headers=headers)
    print(r.status_code, r.reason, r.json())


if __name__ == '__main__':
    send_log()
